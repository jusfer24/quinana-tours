"""API pública de solo lectura del catálogo, para el sitio Astro.

Astro la consulta al generar la página (SSG), así que no necesita sesión ni CSRF.
Solo expone lo que se publica en el sitio; la edición sigue siendo exclusiva del CRM.

- /api/destinos/    Regiones del sitio: nombre y frase (es/en), foto y su crédito.
- /api/categorias/  Tipos de viaje (es/en) con su slug, que es la clave del filtro del sitio,
                    y su ícono (el trazo SVG, para que el sitio dibuje el mismo que el CRM).
- /api/tours/       Tours con su foto (vacía si el tour usa la de su destino) y los slugs
                    de sus categorías.

Las fotos van con URL absoluta (Astro las descarga y optimiza al compilar).
"""

from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Categoria, Destination, Tour


class PublicDestinationSerializer(serializers.ModelSerializer):
    credito = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = ["id", "name", "name_en", "frase", "frase_en", "foto", "foto_alt", "foto_alt_en", "credito"]

    def get_credito(self, destino):
        if not destino.tiene_credito:
            return None
        return {
            "tema": destino.credito_tema or destino.name,
            "autor": destino.credito_autor,
            "licencia": destino.credito_licencia,
            "url": destino.credito_url,
        }


class PublicCategoriaSerializer(serializers.ModelSerializer):
    icono_svg = serializers.CharField(read_only=True)

    class Meta:
        model = Categoria
        fields = ["id", "slug", "nombre", "nombre_en", "icono", "icono_svg"]


class PublicTourSerializer(serializers.ModelSerializer):
    destination = serializers.CharField(source="destination.name")
    duration_label = serializers.CharField()
    categorias = serializers.SlugRelatedField(many=True, read_only=True, slug_field="slug")

    class Meta:
        model = Tour
        fields = [
            "id", "title", "destination", "duration_days", "duration_label", "description", "price_usd",
            "foto", "foto_alt", "categorias",
        ]


class PublicDestinationListView(ListAPIView):
    queryset = Destination.objects.all()
    serializer_class = PublicDestinationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # catálogo público: no lee la sesión


class PublicCategoriaListView(ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = PublicCategoriaSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class PublicTourListView(ListAPIView):
    queryset = Tour.objects.select_related("destination").prefetch_related("categorias")
    serializer_class = PublicTourSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
