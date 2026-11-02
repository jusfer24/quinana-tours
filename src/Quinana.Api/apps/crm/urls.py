"""Rutas del panel interno (/crm/)."""

from django.urls import include, path

from .views import InicioView

urlpatterns = [
    path("", InicioView.as_view(), name="crm_inicio"),
    path("catalogo/tours/", include("tours.urls")),
]
