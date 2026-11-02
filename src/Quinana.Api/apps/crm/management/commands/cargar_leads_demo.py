"""Carga cotizaciones de ejemplo para probar el CRM en local.

Ejecutar con:  python manage.py cargar_leads_demo
               python manage.py cargar_leads_demo --borrar   (solo elimina las de ejemplo)

Necesita el catálogo (python manage.py cargar_catalogo) y al menos un usuario del
personal. Las cotizaciones de ejemplo usan correos @demo.quinana.test: al volver a
correrlo se reemplazan, sin tocar las cotizaciones reales.
"""

import random
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

NOMBRES = ["Olivia", "Liam", "Emma", "Noah", "Mia", "Lucas", "Chloé", "Matteo", "Sofia", "Jonas",
           "Hanna", "Ethan", "Léa", "Oscar", "Ava", "Felix", "Isabel", "Daniel", "Clara", "Marco"]
APELLIDOS = ["Smith", "Johnson", "Müller", "Dubois", "Rossi", "García", "Brown", "Fischer", "Martin",
             "Wilson", "Lefebvre", "Bianchi", "Taylor", "Schneider", "Moreau", "Anderson", "Romano"]

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

        historicas = self.cargar_historicas(tours, equipo, ahora, hoy)
        self.stdout.write(self.style.SUCCESS(
            f"{len(LEADS) + historicas} cotizaciones de ejemplo cargadas "
            f"({borradas} anteriores reemplazadas)."
        ))

    def cargar_historicas(self, tours, equipo, ahora, hoy):
        """Cotizaciones de los últimos 6 meses para que el inicio tenga tendencias reales.

        Semilla fija: cada ejecución genera exactamente los mismos datos. Las más antiguas
        tienen más probabilidad de estar cerradas; el tiempo de primera respuesta varía
        (la mayoría en horas, algunas pasan de la meta de 24 h).
        """
        azar = random.Random(2026)
        origenes = (
            ["Sitio web"] * 14 + ["WhatsApp"] * 4
            + ["Email"] * 2 + ["Referido"] * 2 + ["Redes sociales"] * 2 + ["Feria / evento"]
        )
        creadas = 0
        for n in range(80):
            # Algo más de solicitudes en los meses recientes (la demanda viene creciendo).
            dias_atras = int(azar.triangular(0, 200, 70))
            creada = ahora - timedelta(days=dias_atras, hours=azar.randint(0, 23))
            nombre = f"{azar.choice(NOMBRES)} {azar.choice(APELLIDOS)}"
            email = f"{slugify(nombre).replace('-', '.')}.{n}{DOMINIO}"
            pax = azar.choice([1, 2, 2, 2, 3, 4, 4, 5, 6])
            responsable = azar.choice(equipo)
            respuesta_h = azar.lognormvariate(1.8, 0.9)  # mediana ≈ 6 h
            cierre = None
            if dias_atras > 45 or (dias_atras > 7 and azar.random() < dias_atras / 60):
                etapa = Estado.CERRADA
                resultado = azar.choices(
                    [Resultado.GANADA, Resultado.PERDIDA, Resultado.CANCELADA], weights=[38, 47, 15]
                )[0]
                cierre = creada + timedelta(days=azar.randint(4, min(dias_atras - 1, 45)))
            else:
                resultado = None
                # Las "nuevas" son de los últimos días; las demás ya avanzaron en el embudo.
                if dias_atras <= 3:
                    etapa = Estado.NUEVA
                else:
                    etapa = azar.choices(services.ESTADOS_ABIERTOS[1:], weights=[4, 3, 2])[0]
            if etapa == Estado.NUEVA:
                responsable = None if azar.random() < 0.6 else responsable
            if resultado:
                fecha_viaje = cierre.date() + timedelta(days=azar.randint(10, 150))
            else:  # abiertas: el viaje todavía no llega
                fecha_viaje = hoy + timedelta(days=azar.randint(12, 200))

            lead = LeadCotizacion.objects.create(
                nombre_cliente=nombre, email_cliente=email, tour=azar.choice(tours),
                numero_pasajeros=pax, fecha_estimada=fecha_viaje, origen_lead=azar.choice(origenes),
                estado_embudo=etapa, resultado_cierre=resultado, fecha_cierre=cierre,
                motivo_cierre=MOTIVOS[resultado] if resultado else "", responsable=responsable,
                created_at=creada,
            )
            Contacto.objects.create(lead=lead, nombre=nombre, email=email)

            # Historial con fechas coherentes: creación → primera acción → etapas → cierre.
            actividades = [ActividadLead(lead=lead, tipo=ActividadLead.Tipo.CREACION, fecha=creada,
                                         texto=f"Cotización registrada para «{lead.tour}».")]
            if responsable:
                primera = creada + timedelta(hours=respuesta_h)
                if primera < ahora:
                    actividades.append(ActividadLead(
                        lead=lead, autor=responsable, tipo=ActividadLead.Tipo.ASIGNACION, fecha=primera,
                        texto=f"Responsable: {services.nombre_de(responsable)}.",
                    ))
                # Última acción: el cierre, o un seguimiento reciente (algunas quedan quietas).
                ultima = cierre or (ahora - timedelta(days=azar.choice([0, 1, 1, 2, 3, 4, 8]), hours=2))
                if etapa != Estado.NUEVA and ultima < ahora:
                    actividades.append(ActividadLead(
                        lead=lead, autor=responsable, tipo=ActividadLead.Tipo.ESTADO, fecha=ultima,
                        texto=f"Estado: {lead.get_estado_embudo_display()}"
                        + (f" ({lead.get_resultado_cierre_display().lower()})." if resultado else "."),
                    ))
            ActividadLead.objects.bulk_create(actividades)
            creadas += 1
        return creadas
