"""Convierte destination (texto libre) en una relación con Destination y
duration (texto) en duration_days (entero), conservando los datos existentes.
También agrega las restricciones de integridad a nivel de base de datos."""

import re
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models

DEFAULT_DESTINATIONS = ["Galápagos", "Andes", "Amazonía", "Costa"]


def forwards(apps, schema_editor):
    Destination = apps.get_model("tours", "Destination")
    Tour = apps.get_model("tours", "Tour")

    for name in DEFAULT_DESTINATIONS:
        Destination.objects.get_or_create(name=name)

    for tour in Tour.objects.all():
        raw = (tour.destination or "").strip() or "Sin destino"
        existing = Destination.objects.filter(name__iexact=raw).first()
        dest = existing or Destination.objects.create(name=raw)
        tour.destination_fk_id = dest.pk

        match = re.search(r"\d+", tour.duration or "")
        days = int(match.group()) if match else 1
        tour.duration_days = min(max(days, 1), 60)

        if tour.price_usd is None or tour.price_usd <= 0:
            tour.price_usd = Decimal("0.01")
        tour.save()


class Migration(migrations.Migration):

    dependencies = [("tours", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Destination",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="nombre")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "destino", "verbose_name_plural": "destinos", "ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="destination",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"), name="destination_name_ci_unique"
            ),
        ),
        migrations.AddField(
            model_name="tour",
            name="destination_fk",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tours.destination"),
        ),
        migrations.AddField(
            model_name="tour",
            name="duration_days",
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(model_name="tour", name="destination"),
        migrations.RemoveField(model_name="tour", name="duration"),
        migrations.RenameField(model_name="tour", old_name="destination_fk", new_name="destination"),
        migrations.AlterField(
            model_name="tour",
            name="destination",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tours",
                to="tours.destination",
                verbose_name="destino",
            ),
        ),
        migrations.AlterField(
            model_name="tour",
            name="duration_days",
            field=models.PositiveSmallIntegerField(
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(60)],
                verbose_name="duración (días)",
            ),
        ),
        migrations.AlterField(
            model_name="tour",
            name="title",
            field=models.CharField(max_length=200, validators=[django.core.validators.MinLengthValidator(3)], verbose_name="título"),
        ),
        migrations.AlterField(
            model_name="tour",
            name="description",
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(10)], verbose_name="descripción"),
        ),
        migrations.AlterField(
            model_name="tour",
            name="price_usd",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.01")),
                    django.core.validators.MaxValueValidator(Decimal("100000.00")),
                ],
                verbose_name="precio (USD)",
            ),
        ),
        migrations.AlterModelOptions(name="tour", options={"ordering": ["-created_at"]}),
        migrations.AddConstraint(
            model_name="tour",
            constraint=models.CheckConstraint(condition=models.Q(("price_usd__gt", 0)), name="tour_price_gt_0"),
        ),
        migrations.AddConstraint(
            model_name="tour",
            constraint=models.CheckConstraint(condition=models.Q(("duration_days__gte", 1)), name="tour_duration_gte_1"),
        ),
    ]
