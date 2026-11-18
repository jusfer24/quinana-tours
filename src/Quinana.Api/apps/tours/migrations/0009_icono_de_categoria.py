"""Ícono de cada categoría (clave de tours/iconos.py) y el ícono inicial de las cuatro
categorías iniciales: Aventura (mochila), Naturaleza y fauna (hoja), Cultura y Playa (ola).
"""

from django.db import migrations, models

from tours.datos import completar_iconos


def forwards(apps, schema_editor):
    completar_iconos(apps.get_model("tours", "Categoria"))


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0008_categorias_iniciales'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='icono',
            field=models.CharField(blank=True, max_length=30, verbose_name='ícono'),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
