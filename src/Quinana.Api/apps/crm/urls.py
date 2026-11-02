"""Rutas del panel interno (/crm/)."""

from django.urls import include, path

from .views import InicioView, LeadCreateView, LeadDetailView, LeadEmbudoView, LeadListView

urlpatterns = [
    path("", InicioView.as_view(), name="crm_inicio"),
    path("cotizaciones/", LeadListView.as_view(), name="lead_list"),
    path("cotizaciones/embudo/", LeadEmbudoView.as_view(), name="lead_embudo"),
    path("cotizaciones/nueva/", LeadCreateView.as_view(), name="lead_create"),
    path("cotizaciones/<int:pk>/", LeadDetailView.as_view(), name="lead_detail"),
    path("catalogo/tours/", include("tours.urls")),
]
