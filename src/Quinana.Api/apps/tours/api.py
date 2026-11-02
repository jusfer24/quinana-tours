"""API pública de solo lectura del catálogo, para el sitio Astro.

Astro la consulta al generar la página (SSG), así que no necesita sesión ni CSRF.
Solo expone lo que se publica en el sitio; el CRUD sigue siendo exclusivo del panel.
"""

from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Tour


class PublicTourSerializer(serializers.ModelSerializer):
    destination = serializers.CharField(source="destination.name")
    duration_label = serializers.CharField()

    class Meta:
        model = Tour
        fields = ["id", "title", "destination", "duration_days", "duration_label", "description", "price_usd"]


class PublicTourListView(ListAPIView):
    queryset = Tour.objects.select_related("destination")
    serializer_class = PublicTourSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # catálogo público: no lee la sesión
