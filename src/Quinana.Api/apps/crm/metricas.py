"""Indicadores y gráficas del inicio del CRM.

Todo se calcula aquí (consultas + geometría de las gráficas SVG) para que la plantilla
solo dibuje. Las gráficas siguen la guía de visualización del proyecto:
- un solo tono de dato (verde #1b8552, validado) y gris cálido para el contexto;
- barras finas (<= 24 px) con el extremo redondeado y la base recta;
- un solo eje; cada gráfica tiene además su tabla de datos (se abre con "Ver datos").

El periodo (30, 90 o 365 días) acota todo lo que depende de fechas; la lista de
"Requieren atención" muestra el estado de ahora.
"""

import calendar
import math
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from statistics import median

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Min, Q, Sum
from django.utils import dateformat, timezone

from tours.models import ActividadLead, LeadCotizacion


Estado = LeadCotizacion.EstadoEmbudo
Resultado = LeadCotizacion.ResultadoCierre

PERIODOS = {"30": ("30 días", 30), "90": ("90 días", 90), "365": ("12 meses", 365)}
PERIODO_INICIAL = "90"
META_RESPUESTA_HORAS = 24
DIAS_SIN_MOVIMIENTO = 5
DIAS_VIAJE_CERCANO = 30

VALOR = ExpressionWrapper(
    F("tour__price_usd") * F("numero_pasajeros"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


# ---------------------------------------------------------------- utilidades

def variacion(actual, anterior):
    """Cambio porcentual frente al periodo anterior, o None si no hay base para compararlo."""
    if not anterior:
        return None
    return round((float(actual) - float(anterior)) / float(anterior) * 100)


def tope_redondo(valor, marcas=4):
    """Máximo "limpio" del eje Y (pasos de 1, 2 o 5 × 10^n: siempre enteros) y el paso."""
    if valor <= 0:
        return marcas, 1
    paso_crudo = valor / marcas
    potencia = 10 ** math.floor(math.log10(paso_crudo))
    for factor in (1, 2, 5, 10):
        paso = factor * potencia
        if paso * marcas >= valor:
            break
    if paso < 1:
        paso = 1
    return paso * marcas, paso


def usd(valor):
    """$12 450 (separador de miles con espacio fino, sin decimales)."""
    return "$" + f"{float(valor):,.0f}".replace(",", " ")


def columna_redondeada(x, y, ancho, alto, radio=4):
    """Trazo de una columna con el extremo superior redondeado y la base recta."""
    if alto <= 0:
        return ""
    r = min(radio, alto, ancho / 2)
    return (
        f"M{x:.1f},{y + alto:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"H{x + ancho - r:.1f} Q{x + ancho:.1f},{y:.1f} {x + ancho:.1f},{y + r:.1f} V{y + alto:.1f} Z"
    )


def columna_recta(x, y, ancho, alto):
    if alto <= 0:
        return ""
    return f"M{x:.1f},{y + alto:.1f} V{y:.1f} H{x + ancho:.1f} V{y + alto:.1f} Z"


# ---------------------------------------------------------------- tramos de tiempo

def tramos(desde, hasta, dias):
    """Semanas (periodos de hasta 90 días) o meses (12 meses) que cubren el periodo."""
    resultado = []
    if dias <= 90:
        local = timezone.localtime(desde).date()
        lunes = local - timedelta(days=local.weekday())
        inicio = timezone.make_aware(datetime.combine(lunes, time.min))
        while inicio < hasta:
            fin = inicio + timedelta(days=7)
            resultado.append((inicio, fin, dateformat.format(inicio, "j M")))
            inicio = fin
    else:
        local = timezone.localtime(hasta)
        anio, mes = local.year, local.month
        for i in range(11, -1, -1):
            a, m = anio, mes - i
            while m <= 0:
                a, m = a - 1, m + 12
            inicio = timezone.make_aware(datetime(a, m, 1))
            fin_a, fin_m = (a + 1, 1) if m == 12 else (a, m + 1)
            fin = timezone.make_aware(datetime(fin_a, fin_m, 1))
            resultado.append((inicio, fin, dateformat.format(inicio, "M")))
    return resultado


# ---------------------------------------------------------------- gráficas

def grafica_solicitudes(leads, rangos):
    """Columnas apiladas por tramo: ganadas (verde, base) + resto (gris, arriba)."""
    ancho, alto = 1040, 240  # ancho pensado para la tarjeta a todo el ancho del inicio
    izq, abajo, arriba = 34, 26, 12
    alto_plot = alto - abajo - arriba
    datos = []
    for inicio, fin, etiqueta in rangos:
        del_tramo = [lead for lead in leads if inicio <= lead["created_at"] < fin]
        ganadas = sum(1 for lead in del_tramo if lead["resultado_cierre"] == Resultado.GANADA)
        datos.append({"etiqueta": etiqueta, "total": len(del_tramo), "ganadas": ganadas,
                      "resto": len(del_tramo) - ganadas, "inicio": inicio})

    tope, paso = tope_redondo(max((d["total"] for d in datos), default=0))
    banda = (ancho - izq) / max(len(datos), 1)
    grosor = min(24, banda * 0.6)
    escala = alto_plot / tope
    base = arriba + alto_plot
    cada = max(1, math.ceil(len(datos) / 8))  # no más de ~8 etiquetas en el eje X
    for i, d in enumerate(datos):
        x = izq + banda * i + (banda - grosor) / 2
        alto_g = d["ganadas"] * escala
        alto_r = d["resto"] * escala
        hueco = 2 if alto_g and alto_r else 0  # separación de 2 px entre segmentos
        y_g = base - alto_g
        y_r = y_g - hueco - alto_r
        # El extremo redondeado va en el segmento de arriba de la pila.
        d["trazo_ganadas"] = (columna_recta if alto_r else columna_redondeada)(x, y_g, grosor, alto_g)
        d["trazo_resto"] = columna_redondeada(x, y_r, grosor, alto_r)
        d["x_etiqueta"] = x + grosor / 2
        d["mostrar_etiqueta"] = i % cada == 0 or i == len(datos) - 1
        d["hit_x"], d["hit_ancho"] = izq + banda * i, banda
        d["y_valor"] = (y_r if alto_r else y_g) - 6
    marcas = [{"valor": int(v) if float(v).is_integer() else v, "y": base - v * escala}
              for v in [paso * k for k in range(0, int(round(tope / paso)) + 1)]]
    pico = max(datos, key=lambda d: d["total"], default=None)
    return {
        "ancho": ancho, "alto": alto, "izq": izq, "base": base, "arriba": arriba, "alto_plot": alto_plot,
        "y_etiquetas": alto - 8, "datos": datos, "marcas": marcas,
        "pico": pico if pico and pico["total"] else None,
        "total": sum(d["total"] for d in datos), "ganadas": sum(d["ganadas"] for d in datos),
    }


def barras(filas, clave_valor="cantidad"):
    """Barras horizontales (HTML): agrega el ancho relativo de cada fila (0-100 %)."""
    maximo = max((float(f[clave_valor]) for f in filas), default=0) or 1
    for fila in filas:
        fila["pct"] = round(float(fila[clave_valor]) / maximo * 100, 1)
    return filas


def sparkline(valores, ancho=120, alto=34):
    """Tendencia mínima: línea gris con el último punto destacado."""
    if len(valores) < 2:
        return None
    maximo = max(valores) or 1
    paso = ancho / (len(valores) - 1)
    puntos = [(i * paso, alto - 3 - (float(v) / float(maximo)) * (alto - 6)) for i, v in enumerate(valores)]
    return {
        "ancho": ancho, "alto": alto,
        "puntos": " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos),
        "ultimo": {"x": puntos[-1][0], "y": puntos[-1][1]},
    }


# ---------------------------------------------------------------- calendario de viajes

DIAS_SEMANA = ["L", "M", "M", "J", "V", "S", "D"]


def mes_de(texto, hoy):
    """Primer día del mes pedido en la URL (?mes=2026-11); si no es válido, el mes actual."""
    try:
        anio, mes = (int(x) for x in (texto or "").split("-"))
        return date(anio, mes, 1)
    except ValueError:
        return hoy.replace(day=1)


def calendario_viajes(mes_texto, hoy):
    """Mes con las salidas de los viajes ganados y los días que cada grupo está de viaje.

    Un viaje ocupa desde su fecha de salida hasta salida + duración del tour - 1.
    """
    inicio = mes_de(mes_texto, hoy)
    ultimo = date(inicio.year, inicio.month, calendar.monthrange(inicio.year, inicio.month)[1])
    semanas = calendar.Calendar(firstweekday=0).monthdatescalendar(inicio.year, inicio.month)
    primero_vista, ultimo_vista = semanas[0][0], semanas[-1][-1]

    # Viajes que se cruzan con la vista (los que salieron antes pueden seguir en ruta).
    ganadas = (
        LeadCotizacion.objects.filter(
            resultado_cierre=Resultado.GANADA,
            fecha_estimada__lte=ultimo_vista,
            fecha_estimada__gte=primero_vista - timedelta(days=60),
        )
        .select_related("tour")
        .order_by("fecha_estimada", "nombre_cliente")
    )
    salidas, en_ruta = {}, {}
    for lead in ganadas:
        dias = max(lead.tour.duration_days, 1)
        fin = lead.fecha_estimada + timedelta(days=dias - 1)
        if fin < primero_vista:
            continue
        salidas.setdefault(lead.fecha_estimada, []).append(lead)
        for n in range(dias):
            en_ruta.setdefault(lead.fecha_estimada + timedelta(days=n), set()).add(lead.pk)

    def limpio(texto):  # el tooltip separa filas con ";" y columnas con "|"
        return str(texto).replace(";", ",").replace("|", "/")

    filas = []
    for semana in semanas:
        fila = []
        for dia in semana:
            del_dia = salidas.get(dia, [])
            fila.append({
                "fecha": dia,
                "del_mes": dia.month == inicio.month,
                "hoy": dia == hoy,
                "pasado": dia < hoy,
                "salidas": len(del_dia),
                "en_ruta": len(en_ruta.get(dia, ())),
                # Hasta 2 nombres dentro de la celda; el resto se cuenta ("+1 más").
                "chips": [
                    {"pk": lead.pk, "texto": f"{lead.nombre_cliente.split()[0]} · {lead.numero_pasajeros} pax"}
                    for lead in del_dia[:2]
                ],
                "mas": max(len(del_dia) - 2, 0),
                "tip": ";".join(
                    f"{lead.numero_pasajeros} pax|{limpio(lead.nombre_cliente)} · {limpio(lead.tour)}"
                    for lead in del_dia
                ),
            })
        filas.append(fila)

    anterior = (inicio - timedelta(days=1)).replace(day=1)
    siguiente = ultimo + timedelta(days=1)
    del_mes = [lead for dia, leads in sorted(salidas.items()) if dia.month == inicio.month
               and dia.year == inicio.year for lead in leads]
    return {
        "mes": inicio,
        "semanas": filas,
        "dias_semana": DIAS_SEMANA,
        "anterior": anterior.strftime("%Y-%m"),
        "siguiente": siguiente.strftime("%Y-%m"),
        "es_mes_actual": inicio == hoy.replace(day=1),
        "salidas_mes": del_mes,
        "pasajeros_mes": sum(lead.numero_pasajeros for lead in del_mes),
    }


# ---------------------------------------------------------------- panel completo

def panel(user, clave_periodo, mes=None):
    etiqueta_periodo, dias = PERIODOS.get(clave_periodo, PERIODOS[PERIODO_INICIAL])
    ahora = timezone.now()
    hoy = timezone.localdate()
    desde = ahora - timedelta(days=dias)
    antes = desde - timedelta(days=dias)
    leads = LeadCotizacion.objects.annotate(valor=VALOR)

    # --- Indicadores (periodo actual vs anterior)
    recibidas = leads.filter(created_at__gte=desde).count()
    recibidas_antes = leads.filter(created_at__gte=antes, created_at__lt=desde).count()

    cerradas = leads.filter(estado_embudo=Estado.CERRADA, fecha_cierre__gte=desde)
    ganadas = cerradas.filter(resultado_cierre=Resultado.GANADA)
    ganado = ganadas.aggregate(t=Sum("valor"))["t"] or Decimal(0)
    cerradas_antes = leads.filter(estado_embudo=Estado.CERRADA, fecha_cierre__gte=antes, fecha_cierre__lt=desde)
    ganado_antes = cerradas_antes.filter(resultado_cierre=Resultado.GANADA).aggregate(t=Sum("valor"))["t"] or 0

    n_cerradas, n_ganadas = cerradas.count(), ganadas.count()
    conversion = round(n_ganadas / n_cerradas * 100) if n_cerradas else None
    n_cerradas_antes = cerradas_antes.count()
    conversion_antes = (
        round(cerradas_antes.filter(resultado_cierre=Resultado.GANADA).count() / n_cerradas_antes * 100)
        if n_cerradas_antes else None
    )

    # Primera respuesta: de la solicitud a la primera acción de una persona del equipo.
    primeras = (
        leads.filter(created_at__gte=desde)
        .annotate(primera=Min("actividades__fecha", filter=Q(actividades__autor__isnull=False)
                              & ~Q(actividades__tipo=ActividadLead.Tipo.CREACION)))
        .values_list("created_at", "primera")
    )
    horas = [(p - c).total_seconds() / 3600 for c, p in primeras if p]
    sin_respuesta = sum(1 for _, p in primeras if not p)
    mediana_horas = median(horas) if horas else None
    a_tiempo = sum(1 for h in horas if h <= META_RESPUESTA_HORAS)
    pct_a_tiempo = round(a_tiempo / len(primeras) * 100) if primeras else None

    # --- Serie temporal (y las tendencias de los indicadores)
    rangos = tramos(desde, ahora, dias)
    serie = list(
        leads.filter(created_at__gte=rangos[0][0]).values("created_at", "resultado_cierre")
    )
    solicitudes = grafica_solicitudes(serie, rangos)
    ganado_serie = []
    for inicio, fin, _ in rangos:
        ganado_serie.append(
            leads.filter(resultado_cierre=Resultado.GANADA, fecha_cierre__gte=inicio, fecha_cierre__lt=fin)
            .aggregate(t=Sum("valor"))["t"] or 0
        )

    # --- Demanda por destino y origen (periodo)
    del_periodo = leads.filter(created_at__gte=desde)
    destinos = barras([
        {"etiqueta": f["tour__destination__name"], "cantidad": f["cantidad"], "total": f["total"] or 0}
        for f in del_periodo.values("tour__destination__name")
        .annotate(cantidad=Count("id"), total=Sum("valor")).order_by("-cantidad", "tour__destination__name")
    ])
    for fila in destinos:
        fila["total_txt"] = usd(fila["total"])
    origenes = barras([
        {"etiqueta": f["origen_lead"] or "Sin dato", "cantidad": f["cantidad"]}
        for f in del_periodo.values("origen_lead").annotate(cantidad=Count("id")).order_by("-cantidad")
    ][:6])

    # --- Requieren atención (estado de ahora)
    abiertas = leads.exclude(estado_embudo=Estado.CERRADA).select_related("tour", "responsable").annotate(
        ultima=Max("actividades__fecha")
    )
    avisos, vistos = [], set()

    def avisar(lead, motivo, tipo):
        if lead.pk not in vistos:
            vistos.add(lead.pk)
            avisos.append({"lead": lead, "motivo": motivo, "tipo": tipo})

    sin_asignar = abiertas.filter(responsable__isnull=True, created_at__lt=ahora - timedelta(hours=24))
    for lead in sin_asignar.order_by("created_at"):
        horas_espera = int((ahora - lead.created_at).total_seconds() // 3600)
        texto = f"{horas_espera // 24} días" if horas_espera >= 48 else f"{horas_espera} h"
        avisar(lead, f"Sin responsable desde hace {texto}", "urgente")
    proximas = abiertas.filter(fecha_estimada__lte=hoy + timedelta(days=DIAS_VIAJE_CERCANO))
    for lead in proximas.order_by("fecha_estimada"):
        dias_viaje = (lead.fecha_estimada - hoy).days
        texto = "ya pasó la fecha" if dias_viaje < 0 else f"viaja en {dias_viaje} días"
        avisar(lead, f"Sigue abierta y {texto}", "urgente" if dias_viaje <= 14 else "atencion")
    quietas = abiertas.filter(ultima__lt=ahora - timedelta(days=DIAS_SIN_MOVIMIENTO))
    for lead in quietas.order_by("ultima"):
        avisar(lead, f"Sin movimiento hace {(ahora - lead.ultima).days} días", "atencion")

    # --- Calendario de viajes confirmados
    viajes = calendario_viajes(mes, hoy)

    # --- Equipo
    equipo = []
    for persona in get_user_model().objects.filter(is_staff=True, is_active=True):
        propias = leads.filter(responsable=persona)
        ganadas_p = propias.filter(resultado_cierre=Resultado.GANADA, fecha_cierre__gte=desde)
        fila = {
            "nombre": persona.get_full_name() or persona.get_username(),
            "es_yo": persona == user,
            "abiertas": propias.exclude(estado_embudo=Estado.CERRADA).count(),
            "ganadas": ganadas_p.count(),
            "ganado": ganadas_p.aggregate(t=Sum("valor"))["t"] or 0,
        }
        fila["ganado_txt"] = usd(fila["ganado"])
        if fila["abiertas"] or fila["ganadas"]:
            equipo.append(fila)
    equipo.sort(key=lambda f: (-float(f["ganado"]), -f["abiertas"]))

    return {
        "periodo": {"clave": clave_periodo if clave_periodo in PERIODOS else PERIODO_INICIAL,
                    "etiqueta": etiqueta_periodo, "opciones": PERIODOS},
        "kpi": {
            "recibidas": {"valor": recibidas, "variacion": variacion(recibidas, recibidas_antes),
                          "tendencia": sparkline([d["total"] for d in solicitudes["datos"]])},
            "ganado": {"valor": usd(ganado), "variacion": variacion(ganado, ganado_antes),
                       "ventas": n_ganadas, "tendencia": sparkline(ganado_serie)},
            "conversion": {"valor": conversion, "ganadas": n_ganadas, "cerradas": n_cerradas,
                           "diferencia": None if conversion is None or conversion_antes is None
                           else conversion - conversion_antes},
            "respuesta": {
                "horas": None if mediana_horas is None else (round(mediana_horas) if mediana_horas >= 1 else "<1"),
                "meta": META_RESPUESTA_HORAS, "pct_a_tiempo": pct_a_tiempo, "sin_respuesta": sin_respuesta,
                "cumple": mediana_horas is not None and mediana_horas <= META_RESPUESTA_HORAS,
                "medidor": None if mediana_horas is None
                else min(round(mediana_horas / (META_RESPUESTA_HORAS * 2) * 100), 100),
            },
        },
        "solicitudes": solicitudes,
        "destinos": destinos,
        "origenes": origenes,
        "avisos": avisos[:7],
        "avisos_total": len(avisos),
        "viajes": viajes,
        "equipo": equipo,
    }
