"""Contenido inicial del catálogo: los cuatro destinos del sitio público (de oeste a este)
y las categorías (tipos de viaje) de los tours de ejemplo.

Los destinos vivían fijos en el sitio Astro (src/lib/regions.ts); ahora son datos del CRM.
Lo usan las migraciones 0006 (textos de destinos) y 0008 (categorías) y el comando
cargar_catalogo. Solo se completa lo que falta: nunca se pisa lo que el equipo ya editó.

Fotos de Wikimedia Commons (carpeta destinos/). Las CC BY-SA exigen dar crédito.
"""

from pathlib import Path

CARPETA_FOTOS = Path(__file__).resolve().parent / "destinos"

DESTINOS = [
    {
        "name": "Galápagos",
        "name_en": "Galápagos",
        "frase": "Islas encantadas",
        "frase_en": "The Enchanted Isles",
        "foto": "galapagos.jpg",
        "foto_alt": "Dos lobos marinos caminando por la orilla de una playa en la isla Isabela, Galápagos",
        "foto_alt_en": "Two sea lions walking along the shore of a beach on Isabela Island, Galápagos",
        "credito_tema": "Lobos marinos, Isabela",
        "credito_autor": "Charles J. Sharp",
        "credito_licencia": "CC BY-SA 3.0",
        "credito_url": "https://commons.wikimedia.org/wiki/File:Gal%C3%A1pagos_sea_lions_Isabela.jpg",
    },
    {
        "name": "Costa",
        "name_en": "Coast",
        "frase": "Pacífico y ballenas",
        "frase_en": "Pacific beaches and whales",
        "foto": "costa.jpg",
        "foto_alt": "Olas del Pacífico rompiendo en la playa Los Frailes, rodeada de acantilados verdes",
        "foto_alt_en": "Pacific waves breaking on Los Frailes beach, framed by green cliffs",
        "credito_tema": "Playa Los Frailes",
        "credito_autor": "AnitaAD",
        "credito_licencia": "CC BY-SA 4.0",
        "credito_url": "https://commons.wikimedia.org/wiki/File:Playa_Los_Frailes.jpg",
    },
    {
        "name": "Andes",
        "name_en": "Andes",
        "frase": "Volcanes y lagunas",
        "frase_en": "Volcanoes and crater lakes",
        "foto": "andes.jpg",
        "foto_alt": "El volcán Cotopaxi nevado entre nubes, sobre el páramo andino",
        "foto_alt_en": "Snow-capped Cotopaxi volcano among clouds, above the Andean páramo",
        "credito_tema": "Cotopaxi",
        "credito_autor": "Bernard Gagnon",
        "credito_licencia": "CC BY-SA 3.0",
        "credito_url": "https://commons.wikimedia.org/wiki/File:Cotopaxi_01.jpg",
    },
    {
        "name": "Amazonía",
        "name_en": "Amazon",
        "frase": "Selva viva",
        "frase_en": "Living rainforest",
        "foto": "amazonia.jpg",
        "foto_alt": "Pasarela de madera entre árboles gigantes hacia un lodge en la Reserva Cuyabeno",
        "foto_alt_en": "Wooden boardwalk between giant trees leading to a lodge in the Cuyabeno Reserve",
        "credito_tema": "Lodge en Cuyabeno",
        "credito_autor": "Fährtenleser",
        "credito_licencia": "CC0",
        "credito_url": "https://commons.wikimedia.org/wiki/File:Lodge_im_Cuyabeno_Wildtier-Reservat.jpg",
    },
]

CAMPOS_DE_TEXTO = [
    "name_en", "frase", "frase_en", "foto_alt", "foto_alt_en",
    "credito_tema", "credito_autor", "credito_licencia", "credito_url",
]


def completar_destinos(Destination, crear=False, con_fotos=False):
    """Completa los campos vacíos de los cuatro destinos. Devuelve cuántos cambió.

    `Destination` es el modelo (el real o el histórico de una migración).
    `crear` crea los que falten; `con_fotos` sube la foto si el destino no tiene una.
    """
    from django.core.files import File

    cambiados = 0
    for orden, datos in enumerate(DESTINOS, start=1):
        destino = Destination.objects.filter(name__iexact=datos["name"]).first()
        if destino is None:
            if not crear:
                continue
            destino = Destination(name=datos["name"])

        cambios = [campo for campo in CAMPOS_DE_TEXTO if not getattr(destino, campo)]
        for campo in cambios:
            setattr(destino, campo, datos[campo])
        if not destino.orden:
            destino.orden = orden
            cambios.append("orden")
        if con_fotos and not destino.foto:
            with open(CARPETA_FOTOS / datos["foto"], "rb") as archivo:
                destino.foto.save(datos["foto"], File(archivo), save=False)
            cambios.append("foto")

        if cambios or destino.pk is None:
            destino.save()
            cambiados += 1
    return cambiados


CATEGORIAS = [
    {"slug": "aventura", "nombre": "Aventura", "nombre_en": "Adventure", "icono": "mochila"},
    {"slug": "naturaleza", "nombre": "Naturaleza y fauna", "nombre_en": "Nature & wildlife", "icono": "hoja"},
    {"slug": "cultura", "nombre": "Cultura", "nombre_en": "Culture", "icono": "cultura"},
    {"slug": "playa", "nombre": "Playa", "nombre_en": "Beach", "icono": "ola"},
]

# Categorías de los tours de ejemplo (cargar_catalogo), por título.
CATEGORIAS_DE_TOURS = {
    "Galápagos: crucero por las islas centrales": ["naturaleza", "aventura"],
    "Galápagos island hopping": ["naturaleza", "playa"],
    "Laguna del Quilotoa y Cotopaxi": ["aventura", "naturaleza"],
    "Avenida de los Volcanes y Baños": ["aventura", "naturaleza"],
    "Quito colonial y Mitad del Mundo": ["cultura"],
    "Lodge en la Reserva Cuyabeno": ["naturaleza", "cultura"],
    "Río Napo y selva de Tena": ["aventura", "cultura"],
    "Puerto López e Isla de la Plata": ["naturaleza", "playa"],
    "Ruta del Spondylus: Montañita y Puerto López": ["playa", "cultura"],
}


def completar_categorias(Categoria, Tour):
    """Crea las categorías que falten y se las asigna a los tours de ejemplo sin categoría.

    Recibe los modelos (los reales o los históricos de una migración).
    """
    categorias = {}
    for orden, datos in enumerate(CATEGORIAS, start=1):
        categoria, _ = Categoria.objects.get_or_create(
            slug=datos["slug"],
            defaults={"nombre": datos["nombre"], "nombre_en": datos["nombre_en"], "orden": orden},
        )
        categorias[datos["slug"]] = categoria

    for titulo, slugs in CATEGORIAS_DE_TOURS.items():
        tour = Tour.objects.filter(title=titulo).first()
        if tour is not None and not tour.categorias.exists():
            tour.categorias.set([categorias[slug] for slug in slugs])


def completar_iconos(Categoria):
    """Pone el ícono inicial a las categorías iniciales que todavía no tienen uno."""
    for datos in CATEGORIAS:
        Categoria.objects.filter(slug=datos["slug"], icono="").update(icono=datos["icono"])
