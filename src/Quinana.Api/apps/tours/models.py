"""Modelo (M del patrón MVC) del catálogo de tours.

Las reglas de datos viven aquí y en la base de datos (CheckConstraint), no solo en
el navegador: un dato inválido no se puede guardar aunque se desactive JavaScript.
"""



from decimal import Decimal

from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


# ==========================================================
# 1. DESTINO
# ==========================================================

class Destination(models.Model):
    name = models.CharField("nombre", max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "destino"
        verbose_name_plural = "destinos"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="destination_name_ci_unique",
            ),
        ]

    def __str__(self):
        return self.name


# ==========================================================
# 2. CATEGORIA
# ==========================================================

class Categoria(models.Model):
    nombre = models.CharField("nombre", max_length=100)
    slug = models.SlugField("slug", max_length=120, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


# ==========================================================
# 3. TOUR
# ==========================================================

class Tour(models.Model):
    MAX_DURATION_DAYS = 60
    MAX_PRICE_USD = Decimal("100000.00")

    title = models.CharField(
        "título",
        max_length=200,
        validators=[MinLengthValidator(3)],
    )

    destination = models.ForeignKey(
        Destination,
        verbose_name="destino",
        on_delete=models.PROTECT,
        related_name="tours",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="tours",
        verbose_name="categoría",
        null=True,
        blank=True,
    )

    # Usuario administrativo que gestiona el tour.
    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tours_gestionados",
        verbose_name="responsable del catálogo",
    )

    duration_days = models.PositiveSmallIntegerField(
        "duración (días)",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(MAX_DURATION_DAYS),
        ],
    )

    description = models.TextField(
        "descripción",
        validators=[MinLengthValidator(10)],
    )

    price_usd = models.DecimalField(
        "precio (USD)",
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(MAX_PRICE_USD),
        ],
    )

    seo_title = models.CharField(
        "título SEO",
        max_length=200,
        blank=True,
    )
    meta_description = models.CharField(
        "descripción SEO",
        max_length=300,
        blank=True,
    )
    seo_keywords = models.CharField(
        "palabras clave SEO",
        max_length=500,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price_usd__gt=0),
                name="tour_price_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(price_usd__lte=Decimal("100000.00")),
                name="tour_price_lte_max",
            ),
            models.CheckConstraint(
                condition=Q(duration_days__gte=1),
                name="tour_duration_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(duration_days__lte=60),
                name="tour_duration_lte_max",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def duration_label(self):
        days = self.duration_days
        return f"{days} día" if days == 1 else f"{days} días"


# ==========================================================
# 4. DIA_ITINERARIO
# ==========================================================

class DiaItinerario(models.Model):
    numero_dia = models.PositiveSmallIntegerField("número de día")
    titulo_dia = models.CharField("título del día", max_length=200)
    descripcion_detallada = models.TextField("descripción detallada")

    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="itinerario",
    )

    class Meta:
        ordering = ["tour", "numero_dia"]
        verbose_name = "día de itinerario"
        verbose_name_plural = "días de itinerario"
        constraints = [
            models.CheckConstraint(
                condition=Q(numero_dia__gte=1),
                name="itinerary_day_gte_1",
            ),
            models.UniqueConstraint(
                fields=["tour", "numero_dia"],
                name="unique_itinerary_day_per_tour",
            ),
        ]

    def __str__(self):
        return f"{self.tour} - Día {self.numero_dia}"


# ==========================================================
# 5. INCLUSION_EXCLUSION
# ==========================================================

class InclusionExclusion(models.Model):
    class Tipo(models.TextChoices):
        INCLUYE = "INCLUYE", "Incluye"
        NO_INCLUYE = "NO_INCLUYE", "No incluye"

    tipo = models.CharField(
        "tipo",
        max_length=20,
        choices=Tipo.choices,
    )
    descripcion = models.CharField(
        "descripción",
        max_length=300,
    )

    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="inclusiones_exclusiones",
    )

    class Meta:
        verbose_name = "inclusión o exclusión"
        verbose_name_plural = "inclusiones y exclusiones"

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.descripcion}"


# ==========================================================
# 6. IMAGEN_TOUR
# ==========================================================

class ImagenTour(models.Model):
    url_webp = models.URLField("URL de imagen WebP", max_length=500)
    alt_text = models.CharField("texto alternativo", max_length=250)

    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="imagenes",
    )

    def __str__(self):
        return f"Imagen de {self.tour}"


# ==========================================================
# 7. LEAD_COTIZACION
# ==========================================================

class LeadCotizacion(models.Model):

    class EstadoEmbudo(models.TextChoices):
        NUEVA = "NUEVA", "Nueva"
        SEGUIMIENTO = "SEGUIMIENTO", "En seguimiento"
        COTIZADA = "COTIZADA", "Cotizada"
        NEGOCIACION = "NEGOCIACION", "En negociación"
        CERRADA = "CERRADA", "Cerrada"

    class ResultadoCierre(models.TextChoices):
        GANADA = "GANADA", "Ganada"
        PERDIDA = "PERDIDA", "Perdida"
        CANCELADA = "CANCELADA", "Cancelada"

    class EstadoSincronizacion(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADO = "COMPLETADO", "Completado"
        ERROR = "ERROR", "Error"

    # Datos históricos del cliente: se conservan según lo aprobado.
    email_cliente = models.EmailField("email del cliente", max_length=254)
    nombre_cliente = models.CharField("nombre del cliente", max_length=200)

    numero_pasajeros = models.PositiveSmallIntegerField(
        "número de pasajeros",
        validators=[MinValueValidator(1)],
    )
    fecha_estimada = models.DateField("fecha estimada del viaje")

    origen_lead = models.CharField(
        "origen del lead",
        max_length=100,
        blank=True,
    )

    estado_embudo = models.CharField(
        "estado comercial",
        max_length=20,
        choices=EstadoEmbudo.choices,
        default=EstadoEmbudo.NUEVA,
    )

    resultado_cierre = models.CharField(
        "resultado del cierre",
        max_length=20,
        choices=ResultadoCierre.choices,
        null=True,
        blank=True,
    )

    fecha_cierre = models.DateTimeField(
        "fecha de cierre",
        null=True,
        blank=True,
    )
    motivo_cierre = models.TextField(
        "motivo de cierre",
        blank=True,
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cotizaciones_asignadas",
        verbose_name="responsable",
    )

    estado_sincronizacion = models.CharField(
        "estado de sincronización",
        max_length=20,
        choices=EstadoSincronizacion.choices,
        default=EstadoSincronizacion.PENDIENTE,
    )

    hubspot_id = models.CharField(
        "ID externo en HubSpot",
        max_length=100,
        blank=True,
    )
    fecha_ultima_sincronizacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    tour = models.ForeignKey(
        Tour,
        on_delete=models.PROTECT,
        related_name="cotizaciones",
    )

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(numero_pasajeros__gte=1),
                name="lead_passengers_gte_1",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(estado_embudo="CERRADA")
                    | (
                        Q(resultado_cierre__isnull=False)
                        & Q(fecha_cierre__isnull=False)
                    )
                ),
                name="closed_lead_requires_result_and_date",
            ),
            models.CheckConstraint(
                condition=(
                    Q(resultado_cierre__isnull=True)
                    | Q(estado_embudo="CERRADA")
                ),
                name="lead_result_requires_closed_status",
            ),
        ]

    def __str__(self):
        return f"{self.nombre_cliente} - {self.tour}"


# ==========================================================
# 8. CONTACTO
# ==========================================================

class Contacto(models.Model):

    class CanalPreferido(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        TELEFONO = "TELEFONO", "Teléfono"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    lead = models.ForeignKey(
        LeadCotizacion,
        on_delete=models.CASCADE,
        related_name="contactos",
    )

    nombre = models.CharField("nombre", max_length=200)
    email = models.EmailField("email", max_length=254)
    telefono = models.CharField("teléfono", max_length=30, blank=True)

    canal_preferido = models.CharField(
        "canal preferido",
        max_length=20,
        choices=CanalPreferido.choices,
        default=CanalPreferido.EMAIL,
    )

    def __str__(self):
        return f"{self.nombre} ({self.email})"


# ==========================================================
# 9. PASAJERO_DETALLE
# ==========================================================

class PasajeroDetalle(models.Model):
    nombre = models.CharField("nombre", max_length=200)

    edad = models.PositiveSmallIntegerField(
        "edad",
        validators=[MinValueValidator(0), MaxValueValidator(120)],
    )

    requerimientos_dieteticos = models.TextField(
        "requerimientos dietéticos",
        blank=True,
    )

    lead = models.ForeignKey(
        LeadCotizacion,
        on_delete=models.CASCADE,
        related_name="pasajeros",
    )

    def __str__(self):
        return f"{self.nombre} - {self.lead}"


# ==========================================================
# 10. PAGO_HITO
# ==========================================================

class PagoHito(models.Model):

    class TipoPago(models.TextChoices):
        ABONO = "ABONO", "Abono"
        TOTALIDAD = "TOTALIDAD", "Totalidad"

    class EstadoTransaccion(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADA = "APROBADA", "Aprobada"
        FALLIDA = "FALLIDA", "Fallida"
        REEMBOLSADA = "REEMBOLSADA", "Reembolsada"

    monto = models.DecimalField(
        "monto",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    tipo_pago = models.CharField(
        "tipo de pago",
        max_length=20,
        choices=TipoPago.choices,
    )

    estado_transaccion = models.CharField(
        "estado de transacción",
        max_length=20,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.PENDIENTE,
    )

    pasarela = models.CharField("pasarela", max_length=100, blank=True)

    # Guardar solo referencias seguras del proveedor; nunca CVV ni PAN.
    token_referencia = models.CharField(
        "referencia/token del proveedor",
        max_length=255,
    )

    fecha_pago = models.DateTimeField(
        "fecha de pago",
        null=True,
        blank=True,
    )

    lead = models.ForeignKey(
        LeadCotizacion,
        on_delete=models.PROTECT,
        related_name="pagos",
    )

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(monto__gt=0),
                name="payment_amount_gt_0",
            ),
        ]

    def __str__(self):
        return f"{self.tipo_pago} - {self.monto} USD"


# ==========================================================
# 11. EVENTO_COMPORTAMIENTO
# ==========================================================

class EventoComportamiento(models.Model):

    class TipoEvento(models.TextChoices):
        DESC_ITINERARIO = "DESC_ITINERARIO", "Descarga de itinerario"
        PAGO_FALLIDO = "PAGO_FALLIDO", "Pago fallido"
        ABANDONO_COTIZACION = (
            "ABANDONO_COTIZACION",
            "Abandono de cotización",
        )

    tipo_evento = models.CharField(
        "tipo de evento",
        max_length=30,
        choices=TipoEvento.choices,
    )

    session_id = models.CharField(
        "ID de sesión",
        max_length=255,
        blank=True,
    )

    metadata = models.JSONField(
        "metadatos",
        default=dict,
        blank=True,
    )

    timestamp = models.DateTimeField(
        "fecha del evento",
        auto_now_add=True,
    )

    lead = models.ForeignKey(
        LeadCotizacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
    )

    tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tipo_evento", "timestamp"]),
            models.Index(fields=["session_id"]),
        ]

    def __str__(self):
        return f"{self.tipo_evento} - {self.timestamp}"
