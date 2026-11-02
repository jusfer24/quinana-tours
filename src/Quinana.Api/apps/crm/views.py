"""Controladores del panel interno (CRM)."""

from django.views.generic import TemplateView

from tours.models import LeadCotizacion, Tour

from .mixins import StaffRequiredMixin


class InicioView(StaffRequiredMixin, TemplateView):
    """Portada del panel: resumen rápido y accesos directos."""

    template_name = "crm/inicio.html"
    seccion = "inicio"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        abiertas = LeadCotizacion.objects.exclude(estado_embudo=LeadCotizacion.EstadoEmbudo.CERRADA)
        context["resumen"] = {
            "abiertas": abiertas.count(),
            "sin_responsable": abiertas.filter(responsable__isnull=True).count(),
            "mias": abiertas.filter(responsable=self.request.user).count(),
            "tours": Tour.objects.count(),
        }
        return context
