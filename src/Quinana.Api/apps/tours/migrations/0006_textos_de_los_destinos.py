"""Pasa a la base de datos los textos de los cuatro destinos que el sitio Astro tenía fijos
(nombre en inglés, frase, descripción de la foto y crédito).

Solo completa campos vacíos de destinos que ya existen. Las fotos no se suben aquí, sino
con `python manage.py cargar_catalogo`: así las pruebas no escriben archivos en media/.
"""

from django.db import migrations

from tours.datos import completar_destinos


def forwards(apps, schema_editor):
    completar_destinos(apps.get_model("tours", "Destination"))


class Migration(migrations.Migration):
    dependencies = [
        ("tours", "0005_destinos_y_fotos_del_sitio"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
