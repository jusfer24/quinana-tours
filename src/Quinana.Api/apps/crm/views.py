"""Controladores del panel interno (CRM)."""

import re

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from tours.models import LeadCotizacion, PagoHito

from . import metricas, services
from .forms import AsignarForm, CerrarForm, EstadoForm, LeadFiltroForm, LeadForm, NotaForm, PagoForm
from .mixins import StaffRequiredMixin

Estado = LeadCotizacion.EstadoEmbudo


class InicioView(StaffRequiredMixin, TemplateView):
    """Inicio del panel: indicadores, gráficas y pendientes del periodo elegido (ver metricas.py)."""

    template_name = "crm/inicio.html"
    seccion = "inicio"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(metricas.panel(
            self.request.user,
            self.request.GET.get("periodo", metricas.PERIODO_INICIAL),
            mes=self.request.GET.get("mes"),
        ))
        return context


# ---------- Cotizaciones ----------

class LeadFiltradoMixin:
    """Lista y embudo comparten los mismos filtros (formulario GET)."""

    def get_filtro(self):
        if not hasattr(self, "_filtro"):
            self._filtro = LeadFiltroForm(self.request.GET or None)
        return self._filtro

    def leads_filtrados(self):
        queryset = LeadCotizacion.objects.select_related("tour", "responsable")
        return self.get_filtro().filtrar(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtro"] = self.get_filtro()
        # Filtros actuales sin la página, para los enlaces de paginación y de cambio de vista.
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class LeadListView(StaffRequiredMixin, LeadFiltradoMixin, ListView):
    template_name = "crm/lead_list.html"
    seccion = "cotizaciones"
    context_object_name = "leads"
    paginate_by = 20

    def get_queryset(self):
        return self.leads_filtrados()


class LeadEmbudoView(StaffRequiredMixin, LeadFiltradoMixin, TemplateView):
    """Embudo: una columna por etapa. Las cerradas solo de los últimos 30 días."""

    template_name = "crm/lead_embudo.html"
    seccion = "cotizaciones"
    DIAS_CERRADAS = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = self.leads_filtrados()
        columnas = []
        for estado in services.ESTADOS_ABIERTOS:
            items = list(leads.filter(estado_embudo=estado).order_by("created_at"))
            for lead in items:
                lead.siguiente = services.siguiente_estado(lead)
            columnas.append({
                "estado": estado,
                "leads": items,
                "valor": sum((lead.valor_estimado for lead in items), 0),
            })
        desde = timezone.now() - timezone.timedelta(days=self.DIAS_CERRADAS)
        cerradas = list(leads.filter(estado_embudo=Estado.CERRADA, fecha_cierre__gte=desde).order_by("-fecha_cierre"))
        columnas.append({
            "estado": Estado.CERRADA,
            "leads": cerradas,
            "ganadas": sum(1 for lead in cerradas if lead.resultado_cierre == LeadCotizacion.ResultadoCierre.GANADA),
        })
        context["columnas"] = columnas
        context["dias_cerradas"] = self.DIAS_CERRADAS
        return context


class LeadCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    """Registrar a mano una cotización que llegó por teléfono, WhatsApp, una feria…"""

    permission_required = "tours.add_leadcotizacion"
    template_name = "crm/lead_form.html"
    seccion = "cotizaciones"
    form_class = LeadForm

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        services.registrar_creacion(self.object, self.request.user)
        if self.object.responsable:
            services.agregar_nota(
                self.object, f"Responsable inicial: {services.nombre_de(self.object.responsable)}.", self.request.user
            )
        messages.success(self.request, f"Cotización de {self.object.nombre_cliente} registrada.")
        return response

    def get_success_url(self):
        return reverse("lead_detail", args=[self.object.pk])


class LeadDetailView(StaffRequiredMixin, DetailView):
    """Ficha de la cotización. Las acciones llegan por POST con un campo "accion"."""

    template_name = "crm/lead_detail.html"
    seccion = "cotizaciones"
    context_object_name = "lead"

    # accion → (formulario, permiso necesario)
    ACCIONES = {
        "estado": (EstadoForm, "tours.change_leadcotizacion"),
        "asignar": (AsignarForm, "tours.change_leadcotizacion"),
        "cerrar": (CerrarForm, "tours.change_leadcotizacion"),
        "reabrir": (None, "tours.change_leadcotizacion"),
        "nota": (NotaForm, "tours.change_leadcotizacion"),
        "pago": (PagoForm, "tours.add_pagohito"),
    }

    def get_queryset(self):
        return LeadCotizacion.objects.select_related("tour__destination", "responsable")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.object
        contactos = list(lead.contactos.all())
        for contacto in contactos:
            contacto.whatsapp = re.sub(r"\D", "", contacto.telefono)
        pagos = list(lead.pagos.all())
        context.update({
            "contactos": contactos,
            "pasajeros": lead.pasajeros.all(),
            "pagos": pagos,
            "total_aprobado": sum(
                (p.monto for p in pagos if p.estado_transaccion == PagoHito.EstadoTransaccion.APROBADA), 0
            ),
            "actividades": lead.actividades.select_related("autor"),
            "siguiente": services.siguiente_estado(lead),
            "viaje_pasado": lead.fecha_estimada < timezone.localdate(),
        })
        # Formularios vacíos (o el que volvió con errores, que llega en kwargs).
        context.setdefault("form_estado", EstadoForm(initial={"estado": lead.estado_embudo}))
        context.setdefault("form_asignar", AsignarForm(initial={"responsable": lead.responsable_id}))
        context.setdefault("form_cerrar", CerrarForm())
        context.setdefault("form_nota", NotaForm())
        context.setdefault("form_pago", PagoForm())
        return context

    def post(self, request, *args, **kwargs):
        self.object = lead = self.get_object()
        accion = request.POST.get("accion")
        if accion not in self.ACCIONES:
            return HttpResponseBadRequest("Acción no válida.")
        form_class, permiso = self.ACCIONES[accion]
        if not request.user.has_perm(permiso):
            raise PermissionDenied

        form = form_class(request.POST) if form_class else None
        if form is not None and not form.is_valid():
            messages.error(request, "Revisa los datos del formulario.")
            context = self.get_context_data(object=lead, **{f"form_{accion}": form})
            return self.render_to_response(context, status=400)

        try:
            mensaje = getattr(self, f"_{accion}")(lead, form, request.user)
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, mensaje)

        # El botón "Avanzar" del embudo vuelve al embudo; lo demás, a la ficha.
        if request.POST.get("volver") == "embudo":
            return redirect(reverse("lead_embudo") + "?" + request.POST.get("filtros", ""))
        return redirect("lead_detail", pk=lead.pk)

    # Cada acción aplica el cambio (services) y devuelve el mensaje de confirmación.
    def _estado(self, lead, form, user):
        services.cambiar_estado(lead, form.cleaned_data["estado"], user)
        return f"{lead.nombre_cliente}: ahora «{lead.get_estado_embudo_display()}»."

    def _asignar(self, lead, form, user):
        services.asignar(lead, form.cleaned_data["responsable"], user)
        return f"Responsable: {services.nombre_de(lead.responsable)}."

    def _cerrar(self, lead, form, user):
        services.cerrar(lead, form.cleaned_data["resultado"], form.cleaned_data["motivo"].strip(), user)
        return f"Cotización cerrada como {lead.get_resultado_cierre_display().lower()}."

    def _reabrir(self, lead, form, user):
        services.reabrir(lead, user)
        return "Cotización reabierta: vuelve a «En seguimiento»."

    def _nota(self, lead, form, user):
        services.agregar_nota(lead, form.cleaned_data["texto"], user)
        return "Nota agregada al historial."

    def _pago(self, lead, form, user):
        services.registrar_pago(lead, form.save(commit=False), user)
        return "Pago registrado."

