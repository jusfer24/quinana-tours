from django.urls import path
from .views import TourListView, TourCreateView, TourUpdateView, TourDeleteView

urlpatterns = [
    path('', TourListView.as_view(), name='tour_list'),
    path('nuevo/', TourCreateView.as_view(), name='tour_create'),
    path('editar/<int:pk>/', TourUpdateView.as_view(), name='tour_update'),
    path('eliminar/<int:pk>/', TourDeleteView.as_view(), name='tour_delete'),
]