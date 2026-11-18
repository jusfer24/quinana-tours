from django.urls import path

from .views import (
    CategoriaCreateView,
    CategoriaDeleteView,
    CategoriaListView,
    CategoriaUpdateView,
    DestinationCreateView,
    DestinationDeleteView,
    DestinationListView,
    DestinationUpdateView,
    TourCreateView,
    TourDeleteView,
    TourListView,
    TourUpdateView,
)

urlpatterns = [
    path('', TourListView.as_view(), name='tour_list'),
    path('nuevo/', TourCreateView.as_view(), name='tour_create'),
    path('editar/<int:pk>/', TourUpdateView.as_view(), name='tour_update'),
    path('eliminar/<int:pk>/', TourDeleteView.as_view(), name='tour_delete'),
]

# /crm/catalogo/destinos/ (ver crm/urls.py)
destino_urlpatterns = [
    path('', DestinationListView.as_view(), name='destino_list'),
    path('nuevo/', DestinationCreateView.as_view(), name='destino_create'),
    path('editar/<int:pk>/', DestinationUpdateView.as_view(), name='destino_update'),
    path('eliminar/<int:pk>/', DestinationDeleteView.as_view(), name='destino_delete'),
]

# /crm/catalogo/categorias/ (ver crm/urls.py)
categoria_urlpatterns = [
    path("", CategoriaListView.as_view(), name="categoria_list"),
    path("nueva/", CategoriaCreateView.as_view(), name="categoria_create"),
    path("editar/<int:pk>/", CategoriaUpdateView.as_view(), name="categoria_update"),
    path("eliminar/<int:pk>/", CategoriaDeleteView.as_view(), name="categoria_delete"),
]
