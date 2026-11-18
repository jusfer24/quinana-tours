"""Crea las categorías iniciales (Aventura, Naturaleza y fauna, Cultura, Playa) y se las
asigna a los tours de ejemplo que ya existan sin categoría. Ver tours/datos.
"""

from django.db import migrations

from tours.datos import completar_categorias


def forwards(apps, schema_editor):
    completar_categorias(apps.get_model("tours", "Categoria"), apps.get_model("tours", "Tour"))


class Migration(migrations.Migration):
    dependencies = [
        ("tours", "0007_categorias_multiples"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
