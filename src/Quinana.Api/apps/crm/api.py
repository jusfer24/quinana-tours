"""API pública para solicitar una cotización desde el sitio Astro (formulario "Solicitar cotización").

No pide sesión: cualquier visitante puede enviarla. Se protege con:
- CSRF: el sitio pide el token en /api/auth/csrf/ y lo manda en X-CSRFToken (igual que el login).
- Límite de envíos por IP (DEFAULT_THROTTLE_RATES["cotizaciones"] en settings).
- Campo trampa "website": invisible para personas; si llega con algo, es un bot y se
  responde 201 sin guardar nada (así el bot no aprende a esquivarlo).

Cada solicitud crea la cotización (estado "Nueva"), su contacto principal y la primera
entrada del historial, y aparece en el CRM con el aviso de "nuevas".
"""

from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from tours.models import Contacto, LeadCotizacion, Tour

from . import services

MAX_PASAJEROS = 30
ORIGEN = "Sitio web"


class SolicitudCotizacionSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=200, trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True)
    tour = serializers.PrimaryKeyRelatedField(queryset=Tour.objects.all())
    pasajeros = serializers.IntegerField(min_value=1, max_value=MAX_PASAJEROS)
    fecha = serializers.DateField()
    mensaje = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)  # campo trampa

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mensajes = {
            "nombre": {"blank": "Escribe tu nombre."},
            "email": {"invalid": "Escribe un correo válido.", "blank": "Escribe tu correo."},
            "tour": {"does_not_exist": "Elige un tour de la lista.", "incorrect_type": "Elige un tour de la lista."},
            "pasajeros": {
                "min_value": "Debe viajar al menos una persona.",
                "max_value": f"Para grupos de más de {MAX_PASAJEROS} personas, escríbenos directamente.",
            },
            "fecha": {"invalid": "Elige una fecha válida."},
        }
        for campo, errores in mensajes.items():
            self.fields[campo].error_messages.update(errores)
            self.fields[campo].error_messages.setdefault("required", "Este campo es obligatorio.")

    def validate_nombre(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Escribe tu nombre.")
        return value

    def validate_fecha(self, value):
        if value <= timezone.localdate():
            raise serializers.ValidationError("Elige una fecha a partir de mañana.")
        return value

    def validate_telefono(self, value):
        value = value.strip()
        if value and sum(c.isdigit() for c in value) < 7:
            raise serializers.ValidationError("Escribe un teléfono con código de país, por ejemplo +1 415 555 0134.")
        return value

    @transaction.atomic
    def create(self, data):
        lead = LeadCotizacion.objects.create(
            nombre_cliente=data["nombre"],
            email_cliente=data["email"].lower(),
            tour=data["tour"],
            numero_pasajeros=data["pasajeros"],
            fecha_estimada=data["fecha"],
            mensaje=data.get("mensaje", "").strip(),
            origen_lead=ORIGEN,
        )
        telefono = data.get("telefono", "")
        Contacto.objects.create(
            lead=lead,
            nombre=lead.nombre_cliente,
            email=lead.email_cliente,
            telefono=telefono,
            canal_preferido=Contacto.CanalPreferido.WHATSAPP if telefono else Contacto.CanalPreferido.EMAIL,
        )
        services.registrar_creacion(lead, None)
        return lead


@method_decorator(csrf_protect, name="dispatch")
class SolicitudCotizacionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cotizaciones"

    def post(self, request):
        if request.data.get("website"):
            return Response(status=status.HTTP_201_CREATED)  # bot: se ignora en silencio
        serializer = SolicitudCotizacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
