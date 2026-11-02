"""Carga cotizaciones de ejemplo para probar el CRM en local.

Ejecutar con:  python manage.py cargar_leads_demo
               python manage.py cargar_leads_demo --borrar   (solo elimina las de ejemplo)

Necesita el catálogo (python manage.py cargar_catalogo) y al menos un usuario del
personal. Las cotizaciones de ejemplo usan correos @demo.quinana.test: al volver a
correrlo se reemplazan, sin tocar las cotizaciones reales.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from crm import services
from tours.models import ActividadLead, Contacto, LeadCotizacion, PagoHito, PasajeroDetalle, Tour

DOMINIO = "@demo.quinana.test"
Estado = LeadCotizacion.EstadoEmbudo
Resultado = LeadCotizacion.ResultadoCierre

# (nombre, teléfono, pasajeros, días desde la solicitud, días hasta el viaje, etapa, resultado, origen, mensaje)
LEADS = [
    ("Emily Carter", "+1 415 555 0134", 2, 0, 75, Estado.NUEVA, None, "Sitio web",
     "We are celebrating our honeymoon and would love a private guide in Galápagos."),
    ("Lukas Weber", "+49 151 2345 6789", 4, 1, 120, Estado.NUEVA, None, "Sitio web",
     "Familie mit zwei Kindern (8 und 11). Interesse an Amazonas und Vulkanen."),
    ("Sophie Martin", "", 2, 3, 40, Estado.NUEVA, None, "Email",
     "Nous cherchons un circuit de 10 jours entre les Andes et la côte."),
    ("James O'Connor", "+44 7700 900123", 6, 2, 25, Estado.SEGUIMIENTO, None, "WhatsApp",
     "Group of friends, mostly interested in hiking Cotopaxi and Quilotoa."),
    ("Ana Lucía Pérez", "+34 612 345 678", 3, 6, 60, Estado.SEGUIMIENTO, None, "Referido",
     "Viajo con mis padres mayores: necesitamos ritmo tranquilo y hoteles cómodos."),
    ("Michael Chen", "+1 647 555 0199", 2, 9, 90, Estado.COTIZADA, None, "Sitio web",
     "Interested in a luxury cruise. Budget is flexible."),
    ("Giulia Rossi", "+39 333 123 4567", 2, 12, 50, Estado.COTIZADA, None, "Redes sociales",
     "Ci interessa la fotografia naturalistica."),
    ("Robert & Linda Hayes", "+1 212 555 0172", 2, 15, 35, Estado.NEGOCIACION, None, "Teléfono",
     "Asking for a 10% discount if we book two tours together."),
    ("Thomas Dubois", "+33 6 12 34 56 78", 5, 25, 20, Estado.CERRADA, Resultado.GANADA, "Sitio web",
     "Voyage d'entreprise pour cinq personnes."),
    ("Hannah Schmidt", "+49 160 9876 5432", 2, 20, 45, Estado.CERRADA, Resultado.PERDIDA, "Sitio web",
     "Wir vergleichen noch Angebote."),
    ("David Miller", "+1 303 555 0110", 1, 18, 10, Estado.CERRADA, Resultado.CANCELADA, "Email",
     "Solo traveler, flexible dates."),
]

MOTIVOS = {
    Resultado.GANADA: "",
    Resultado.PERDIDA: "Eligió otra operadora con un precio más bajo.",
    Resultado.CANCELADA: "El cliente pospuso el viaje por motivos de trabajo.",
}


class Command(BaseCommand):
    help = "Carga cotizaciones de ejemplo (correos @demo.quinana.test) para probar el CRM."

    def add_arguments(self, parser):
        parser.add_argument("--borrar", action="store_true", help="Solo elimina las cotizaciones de ejemplo.")

    @transaction.atomic
    def handle(self, *args, **options):
        demo = LeadCotizacion.objects.filter(email_cliente__endswith=DOMINIO)
        PagoHito.objects.filter(lead__in=demo).delete()  # PROTECT: los pagos se borran antes
        borradas = demo.count()
        demo.delete()
        if options["borrar"]:
            self.stdout.write(self.style.SUCCESS(f"{borradas} cotizaciones de ejemplo eliminadas."))
            return

        tours = list(Tour.objects.order_by("id"))
        if not tours:
            raise CommandError("No hay tours. Ejecuta antes: python manage.py cargar_catalogo")
        equipo = list(get_user_model().objects.filter(is_staff=True, is_active=True).order_by("id"))
        if not equipo:
            raise CommandError("No hay usuarios del personal. Crea uno con: python manage.py createsuperuser")

        ahora = timezone.now()
        hoy = timezone.localdate()
        for i, (nombre, telefono, pax, hace, faltan, etapa, resultado, origen, mensaje) in enumerate(LEADS):
            responsable = None if etapa == Estado.NUEVA else equipo[i % len(equipo)]
            email = slugify(nombre).replace("-", ".") + DOMINIO
            lead = LeadCotizacion.objects.create(
                nombre_cliente=nombre,
                email_cliente=email,
                tour=tours[i % len(tours)],
                numero_pasajeros=pax,
                fecha_estimada=hoy + timedelta(days=faltan),
                origen_lead=origen,
                mensaje=mensaje,
                created_at=ahora - timedelta(days=hace, hours=i),
            )
            Contacto.objects.create(
                lead=lead, nombre=nombre, email=email, telefono=telefono,
                canal_preferido=Contacto.CanalPreferido.WHATSAPP if telefono else Contacto.CanalPreferido.EMAIL,
            )
            for n in range(min(pax, 2)):
                PasajeroDetalle.objects.create(
                    lead=lead, nombre=f"{nombre.split()[0]} (pasajero {n + 1})", edad=30 + 7 * n,
                    requerimientos_dieteticos="Vegetariano" if n == 1 else "",
                )

            # Historial como lo habría ido dejando el equipo.
            services.registrar_creacion(lead, None)
            if responsable:
                services.asignar(lead, responsable, responsable)
                services.agregar_nota(lead, "Primer contacto: se envió el itinerario base.", responsable)
            for paso in services.ESTADOS_ABIERTOS[1:]:
                if etapa == Estado.CERRADA or services.ESTADOS_ABIERTOS.index(paso) <= services.ESTADOS_ABIERTOS.index(etapa):
                    services.cambiar_estado(lead, paso, responsable)
            if resultado:
                if resultado == Resultado.GANADA:
                    services.registrar_pago(lead, PagoHito(
                        monto=(lead.valor_estimado * Decimal("0.3")).quantize(Decimal("0.01")),
                        tipo_pago=PagoHito.TipoPago.ABONO,
                        estado_transaccion=PagoHito.EstadoTransaccion.APROBADA,
                        pasarela="Transferencia",
                        token_referencia=f"TRF-{1000 + i}",
                        fecha_pago=ahora - timedelta(days=2),
                    ), responsable)
                services.cerrar(lead, resultado, MOTIVOS[resultado], responsable)

            # Reparte las fechas del historial entre la solicitud y hoy (antes quedaban todas "ahora").
            actividades = list(lead.actividades.order_by("id"))
            paso_horas = max(hace * 24 // max(len(actividades), 1), 1)
            for n, actividad in enumerate(actividades):
                ActividadLead.objects.filter(pk=actividad.pk).update(
                    fecha=lead.created_at + timedelta(hours=paso_horas * n)
                )

        self.stdout.write(self.style.SUCCESS(
            f"{len(LEADS)} cotizaciones de ejemplo cargadas ({borradas} anteriores reemplazadas)."
        ))
