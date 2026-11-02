"""Acciones sobre las cotizaciones del CRM.

Cada acción guarda el cambio y deja su rastro en el historial (ActividadLead) dentro de
la misma transacción: si algo falla, no queda ni el cambio ni la actividad a medias.
Las vistas solo validan formularios y llaman a estas funciones.
"""

from django.db import transaction
from django.utils import timezone

from tours.models import ActividadLead, LeadCotizacion

Estado = LeadCotizacion.EstadoEmbudo

# Orden del embudo para el botón "Avanzar" (la última etapa se cierra con resultado).
ESTADOS_ABIERTOS = [Estado.NUEVA, Estado.SEGUIMIENTO, Estado.COTIZADA, Estado.NEGOCIACION]


def nombre_de(user):
    if user is None:
        return "nadie"
    return user.get_full_name() or user.get_username()


def siguiente_estado(lead):
    """Etapa abierta que sigue a la actual, o None si ya está en la última o cerrada."""
    if lead.estado_embudo not in ESTADOS_ABIERTOS:
        return None
    i = ESTADOS_ABIERTOS.index(lead.estado_embudo)
    return ESTADOS_ABIERTOS[i + 1] if i + 1 < len(ESTADOS_ABIERTOS) else None


def _registrar(lead, autor, tipo, texto):
    return ActividadLead.objects.create(lead=lead, autor=autor, tipo=tipo, texto=texto)


@transaction.atomic
def registrar_creacion(lead, autor):
    texto = f"Cotización registrada para «{lead.tour}»"
    if lead.origen_lead:
        texto += f" (origen: {lead.origen_lead})"
    _registrar(lead, autor, ActividadLead.Tipo.CREACION, texto + ".")


@transaction.atomic
def cambiar_estado(lead, nuevo, autor):
    """Mueve una cotización abierta a otra etapa abierta (cerrar tiene su propia acción)."""
    if lead.esta_cerrada:
        raise ValueError("La cotización está cerrada: reábrela antes de cambiar su estado.")
    if nuevo not in ESTADOS_ABIERTOS:
        raise ValueError("Para cerrar la cotización usa «Cerrar cotización».")
    if nuevo == lead.estado_embudo:
        return
    anterior = lead.get_estado_embudo_display()
    lead.estado_embudo = nuevo
    lead.save(update_fields=["estado_embudo"])
    _registrar(
        lead, autor, ActividadLead.Tipo.ESTADO,
        f"Estado: {anterior} → {lead.get_estado_embudo_display()}.",
    )


@transaction.atomic
def asignar(lead, responsable, autor):
    if responsable == lead.responsable:
        return
    lead.responsable = responsable
    lead.save(update_fields=["responsable"])
    texto = f"Responsable: {nombre_de(responsable)}." if responsable else "Se quitó el responsable."
    _registrar(lead, autor, ActividadLead.Tipo.ASIGNACION, texto)


@transaction.atomic
def cerrar(lead, resultado, motivo, autor):
    if lead.esta_cerrada:
        raise ValueError("La cotización ya está cerrada.")
    lead.estado_embudo = Estado.CERRADA
    lead.resultado_cierre = resultado
    lead.fecha_cierre = timezone.now()
    lead.motivo_cierre = motivo
    lead.save(update_fields=["estado_embudo", "resultado_cierre", "fecha_cierre", "motivo_cierre"])
    texto = f"Cerrada como {lead.get_resultado_cierre_display().lower()}."
    if motivo:
        texto += f" Motivo: {motivo}"
    _registrar(lead, autor, ActividadLead.Tipo.ESTADO, texto)


@transaction.atomic
def reabrir(lead, autor):
    """Vuelve a "En seguimiento"; el resultado anterior queda en el historial."""
    if not lead.esta_cerrada:
        raise ValueError("La cotización no está cerrada.")
    anterior = lead.get_resultado_cierre_display()
    lead.estado_embudo = Estado.SEGUIMIENTO
    lead.resultado_cierre = None
    lead.fecha_cierre = None
    lead.motivo_cierre = ""
    lead.save(update_fields=["estado_embudo", "resultado_cierre", "fecha_cierre", "motivo_cierre"])
    _registrar(
        lead, autor, ActividadLead.Tipo.ESTADO,
        f"Reabierta (antes: cerrada como {anterior.lower()}). Estado: En seguimiento.",
    )


@transaction.atomic
def agregar_nota(lead, texto, autor):
    _registrar(lead, autor, ActividadLead.Tipo.NOTA, texto)


@transaction.atomic
def registrar_pago(lead, pago, autor):
    """Guarda un PagoHito (formulario sin el lead) y lo anota en el historial."""
    pago.lead = lead
    pago.save()
    _registrar(
        lead, autor, ActividadLead.Tipo.PAGO,
        f"{pago.get_tipo_pago_display()} de ${pago.monto} USD "
        f"({pago.get_estado_transaccion_display().lower()}), ref. {pago.token_referencia}.",
    )
    return pago
