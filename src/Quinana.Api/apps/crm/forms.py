"""Formularios del CRM: filtros de la lista, nueva cotización y acciones del detalle."""

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from tours.models import Contacto, LeadCotizacion, PagoHito, Tour

from .services import ESTADOS_ABIERTOS

Estado = LeadCotizacion.EstadoEmbudo


def personal():
    """Usuarios que pueden ser responsables de una cotización: el personal activo."""
    return get_user_model().objects.filter(is_staff=True, is_active=True).order_by("first_name", "username")


class PersonalChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, user):
        return user.get_full_name() or user.get_username()


class EstiloPanelMixin:
    """Aplica la clase visual del panel (form-input) a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-input")


# ---------- Filtros de la lista y del embudo (GET) ----------

class LeadFiltroForm(EstiloPanelMixin, forms.Form):
    RESPONSABLE_YO = "yo"
    RESPONSABLE_SIN = "sin"

    q = forms.CharField(
        label="Buscar", required=False,
        widget=forms.SearchInput(attrs={"placeholder": "Nombre o email del cliente"}),
    )
    estado = forms.ChoiceField(label="Estado", required=False)
    responsable = forms.ChoiceField(label="Responsable", required=False)
    tour = forms.ModelChoiceField(
        label="Tour", required=False, queryset=Tour.objects.order_by("title"), empty_label="Todos",
    )
    desde = forms.DateField(label="Viaje desde", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    hasta = forms.DateField(label="Viaje hasta", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado"].choices = [("", "Todos"), ("abiertas", "Abiertas")] + list(Estado.choices)
        self.fields["responsable"].choices = [
            ("", "Todos"),
            (self.RESPONSABLE_YO, "Asignadas a mí"),
            (self.RESPONSABLE_SIN, "Sin responsable"),
        ] + [(str(u.pk), u.get_full_name() or u.get_username()) for u in personal()]

    def filtrar(self, queryset, user):
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data["q"]:
            queryset = queryset.filter(
                Q(nombre_cliente__icontains=data["q"]) | Q(email_cliente__icontains=data["q"])
            )
        if data["estado"] == "abiertas":
            queryset = queryset.exclude(estado_embudo=Estado.CERRADA)
        elif data["estado"]:
            queryset = queryset.filter(estado_embudo=data["estado"])
        if data["responsable"] == self.RESPONSABLE_YO:
            queryset = queryset.filter(responsable=user)
        elif data["responsable"] == self.RESPONSABLE_SIN:
            queryset = queryset.filter(responsable__isnull=True)
        elif data["responsable"]:
            queryset = queryset.filter(responsable_id=data["responsable"])
        if data["tour"]:
            queryset = queryset.filter(tour=data["tour"])
        if data["desde"]:
            queryset = queryset.filter(fecha_estimada__gte=data["desde"])
        if data["hasta"]:
            queryset = queryset.filter(fecha_estimada__lte=data["hasta"])
        return queryset

    @property
    def activo(self):
        """True si hay algún filtro aplicado (para mostrar "Quitar filtros")."""
        return self.is_valid() and any(self.cleaned_data.values())


# ---------- Nueva cotización (registrada a mano por el equipo) ----------

ORIGENES = ["Teléfono", "WhatsApp", "Email", "Redes sociales", "Referido", "Feria / evento", "Sitio web", "Otro"]


class LeadForm(EstiloPanelMixin, forms.ModelForm):
    """Cotización que llega por teléfono, WhatsApp, etc. Crea también el contacto principal."""

    telefono = forms.CharField(label="Teléfono / WhatsApp", max_length=30, required=False)
    canal_preferido = forms.ChoiceField(
        label="Canal preferido", choices=Contacto.CanalPreferido.choices, initial=Contacto.CanalPreferido.EMAIL,
    )
    origen_lead = forms.ChoiceField(label="¿Cómo llegó?", choices=[(o, o) for o in ORIGENES])
    responsable = PersonalChoiceField(label="Responsable", queryset=personal(), required=False, empty_label="Sin asignar")

    class Meta:
        model = LeadCotizacion
        fields = [
            "nombre_cliente", "email_cliente", "tour", "numero_pasajeros",
            "fecha_estimada", "origen_lead", "mensaje", "responsable",
        ]
        widgets = {
            "fecha_estimada": forms.DateInput(attrs={"type": "date"}),
            "mensaje": forms.Textarea(attrs={"rows": 3, "placeholder": "Qué busca el cliente, dudas, presupuesto…"}),
            "numero_pasajeros": forms.NumberInput(attrs={"min": "1"}),
        }
        labels = {"nombre_cliente": "Nombre del cliente", "email_cliente": "Email del cliente"}

    field_order = [
        "nombre_cliente", "email_cliente", "telefono", "canal_preferido", "tour",
        "numero_pasajeros", "fecha_estimada", "origen_lead", "responsable", "mensaje",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = personal()
        self.fields["tour"].queryset = Tour.objects.order_by("title")
        self.fields["tour"].empty_label = "— Selecciona un tour —"

    def save(self, commit=True):
        lead = super().save(commit=commit)
        if commit:
            Contacto.objects.create(
                lead=lead,
                nombre=lead.nombre_cliente,
                email=lead.email_cliente,
                telefono=self.cleaned_data["telefono"],
                canal_preferido=self.cleaned_data["canal_preferido"],
            )
        return lead


# ---------- Acciones del detalle (POST con campo "accion") ----------

class EstadoForm(EstiloPanelMixin, forms.Form):
    estado = forms.ChoiceField(
        label="Mover a",
        choices=[(e.value, e.label) for e in ESTADOS_ABIERTOS],
    )


class AsignarForm(EstiloPanelMixin, forms.Form):
    responsable = PersonalChoiceField(label="Responsable", queryset=personal(), required=False, empty_label="Sin asignar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = personal()


class CerrarForm(EstiloPanelMixin, forms.Form):
    resultado = forms.ChoiceField(label="Resultado", choices=LeadCotizacion.ResultadoCierre.choices)
    motivo = forms.CharField(
        label="Motivo", required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Por qué se ganó o se perdió"}),
    )

    def clean(self):
        data = super().clean()
        if data.get("resultado") != LeadCotizacion.ResultadoCierre.GANADA and not data.get("motivo", "").strip():
            self.add_error("motivo", "Indica el motivo: ayuda a entender por qué se pierden ventas.")
        return data


class NotaForm(EstiloPanelMixin, forms.Form):
    texto = forms.CharField(
        label="Nota",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Llamada, correo enviado, acuerdos con el cliente…"}),
    )

    def clean_texto(self):
        return self.cleaned_data["texto"].strip()


class PagoForm(EstiloPanelMixin, forms.ModelForm):
    class Meta:
        model = PagoHito
        fields = ["monto", "tipo_pago", "estado_transaccion", "pasarela", "token_referencia", "fecha_pago"]
        labels = {
            "monto": "Monto (USD)",
            "pasarela": "Medio de pago",
            "token_referencia": "Referencia",
        }
        widgets = {
            "monto": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "pasarela": forms.TextInput(attrs={"placeholder": "Transferencia, tarjeta, PayPal…"}),
            "token_referencia": forms.TextInput(attrs={"placeholder": "Nº de comprobante o transacción"}),
            "fecha_pago": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }
