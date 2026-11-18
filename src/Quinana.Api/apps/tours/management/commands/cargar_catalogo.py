"""Carga los destinos y tours que muestra el sitio público.

Ejecutar con:  python manage.py cargar_catalogo

Se puede correr varias veces sin duplicar: solo crea lo que falta. El catálogo se edita
en el CRM, así que el comando no toca los tours que ya existen (se buscan por título) y a
los destinos solo les completa los textos y la foto vacíos, y les asigna categoría a los
tours de ejemplo que no tengan ninguna (ver tours/datos). Sirve para
arrancar una base nueva, local o del despliegue, con el catálogo del sitio público.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from tours.datos import DESTINOS, completar_categorias, completar_destinos, completar_iconos
from tours.models import Categoria, Destination, Tour

TOURS = [
    {
        "title": "Galápagos: crucero por las islas centrales",
        "destination": "Galápagos",
        "duration_days": 5,
        "price_usd": "2890.00",
        "description": (
            "Navega entre Santa Cruz, Bartolomé y Seymour Norte a bordo de un yate con guía "
            "naturalista. Snorkel con lobos marinos, piqueros de patas azules y tortugas gigantes."
        ),
    },
    {
        "title": "Galápagos island hopping",
        "destination": "Galápagos",
        "duration_days": 6,
        "price_usd": "2190.00",
        "description": (
            "Recorre Santa Cruz, Isabela y San Cristóbal en lancha, durmiendo en hoteles en "
            "tierra. Playas, volcanes y fauna endémica a tu ritmo."
        ),
    },
    {
        "title": "Laguna del Quilotoa y Cotopaxi",
        "destination": "Andes",
        "duration_days": 3,
        "price_usd": "690.00",
        "description": (
            "Camina por el borde del cráter del Quilotoa y explora el Parque Nacional Cotopaxi, "
            "uno de los volcanes activos más altos del mundo. Noches en haciendas andinas."
        ),
    },
    {
        "title": "Avenida de los Volcanes y Baños",
        "destination": "Andes",
        "duration_days": 5,
        "price_usd": "1190.00",
        "description": (
            "De Quito a Baños por la Avenida de los Volcanes: Cotopaxi, Quilotoa, la Ruta de "
            "las Cascadas y aguas termales al pie del Tungurahua."
        ),
    },
    {
        "title": "Quito colonial y Mitad del Mundo",
        "destination": "Andes",
        "duration_days": 2,
        "price_usd": "390.00",
        "description": (
            "El centro histórico de Quito, Patrimonio de la Humanidad, con sus iglesias y "
            "plazas, y una visita a la línea equinoccial en la Mitad del Mundo."
        ),
    },
    {
        "title": "Lodge en la Reserva Cuyabeno",
        "destination": "Amazonía",
        "duration_days": 4,
        "price_usd": "1150.00",
        "description": (
            "Lodge en plena selva con caminatas guiadas, canoa por lagunas de aguas negras, "
            "delfines rosados y visita a una comunidad siona."
        ),
    },
    {
        "title": "Río Napo y selva de Tena",
        "destination": "Amazonía",
        "duration_days": 4,
        "price_usd": "980.00",
        "description": (
            "Rafting en el río Napo, cascadas, cuevas y cultura kichwa en la Amazonía alta, "
            "a pocas horas de Quito."
        ),
    },
    {
        "title": "Puerto López e Isla de la Plata",
        "destination": "Costa",
        "duration_days": 3,
        "price_usd": "590.00",
        "description": (
            "Avistamiento de ballenas jorobadas (junio a septiembre), la Isla de la Plata y la "
            "playa Los Frailes en el Parque Nacional Machalilla."
        ),
    },
    {
        "title": "Ruta del Spondylus: Montañita y Puerto López",
        "destination": "Costa",
        "duration_days": 5,
        "price_usd": "890.00",
        "description": (
            "Recorre la costa del Pacífico: surf en Montañita, pueblos de pescadores, "
            "gastronomía marina y atardeceres en la Ruta del Spondylus."
        ),
    },
]


class Command(BaseCommand):
    help = "Carga los destinos y tours del sitio público (se puede repetir sin duplicar)."

    @transaction.atomic
    def handle(self, *args, **options):
        completar_destinos(Destination, crear=True, con_fotos=True)
        destinos = {d["name"]: Destination.objects.get(name__iexact=d["name"]) for d in DESTINOS}

        creados = 0
        for data in TOURS:
            if Tour.objects.filter(title=data["title"]).exists():
                continue
            tour = Tour(**{**data, "destination": destinos[data["destination"]], "price_usd": Decimal(data["price_usd"])})
            # full_clean aplica las mismas validaciones del modelo que el CRM.
            tour.full_clean()
            tour.save()
            creados += 1

        completar_categorias(Categoria, Tour)
        completar_iconos(Categoria)

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo listo: {len(destinos)} destinos, {creados} tours creados "
                f"({len(TOURS) - creados} ya existían y no se tocaron)."
            )
        )
