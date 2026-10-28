"""Modelo (M del patrón MVC) del catálogo de tours.

Las reglas de datos viven aquí y en la base de datos (CheckConstraint), no solo en
el navegador: un dato inválido no se puede guardar aunque se desactive JavaScript.
"""


from decimal import Decimal

from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models.functions import Lower


class Destination(models.Model):
    """Destino turístico. Un destino puede tener muchos tours."""

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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price_usd__gt=0),
                name="tour_price_gt_0",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    price_usd__lte=Decimal("100000.00")
                ),
                name="tour_price_lte_max",
            ),
            models.CheckConstraint(
                condition=models.Q(duration_days__gte=1),
                name="tour_duration_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(duration_days__lte=60),
                name="tour_duration_lte_max",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def duration_label(self):
        days = self.duration_days
        return f"{days} día" if days == 1 else f"{days} días"
