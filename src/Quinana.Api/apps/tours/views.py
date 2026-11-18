"""Controladores (C del patrón MVC) del catálogo: tours y destinos.

Forman parte del panel interno (/crm/catalogo/tours/, /destinos/ y /categorias/). Lo que se
edita aquí es lo que muestra el sitio público (lo lee de /api/tours/ y /api/destinos/). Sin sesión, todas las vistas
redirigen a LOGIN_URL: el "Acceso del equipo" del sitio público (/login#equipo).

- Listar: solo el personal (StaffRequiredMixin, is_staff); un viajero recibe 403.
  La plantilla solo muestra "Nuevo tour", "Editar" y "Eliminar" a quien tiene permiso.
- Crear, editar y eliminar: además, PermissionRequiredMixin; sin el permiso del modelo, 403.
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from crm.mixins import StaffRequiredMixin

from .forms import CategoriaForm, DestinationForm, TourForm
from .models import Categoria, Destination, Tour


class FotoMixin:
    """Al guardar, borra del almacenamiento la foto que se reemplazó o se quitó.

    Django no borra archivos por su cuenta: sin esto, cada cambio de foto dejaría la vieja.
    """

    def form_valid(self, form):
        anterior = ""
        if form.instance.pk:
            anterior = type(form.instance).objects.filter(pk=form.instance.pk).values_list("foto", flat=True).first() or ""
        response = super().form_valid(form)
        if anterior and anterior != self.object.foto.name:
            self.object.foto.storage.delete(anterior)
        return response


# R - Read (Listar tours)
class TourListView(StaffRequiredMixin, ListView):
    seccion = "tours"
    model = Tour
    template_name = "tour_list.html"
    context_object_name = "tours"
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("destination").prefetch_related("categorias")


# C - Create (Crear tour)
class TourCreateView(StaffRequiredMixin, PermissionRequiredMixin, FotoMixin, SuccessMessageMixin, CreateView):
    seccion = "tours"
    permission_required = "tours.add_tour"
    model = Tour
    form_class = TourForm
    template_name = "tour_form.html"
    success_url = reverse_lazy("tour_list")
    success_message = "Creado correctamente\nTour «%(title)s»"


# U - Update (Actualizar tour)
class TourUpdateView(StaffRequiredMixin, PermissionRequiredMixin, FotoMixin, SuccessMessageMixin, UpdateView):
    seccion = "tours"
    permission_required = "tours.change_tour"
    model = Tour
    form_class = TourForm
    template_name = "tour_form.html"
    success_url = reverse_lazy("tour_list")
    success_message = "Actualizado correctamente\nTour «%(title)s»"


# D - Delete (Eliminar tour)
class TourDeleteView(StaffRequiredMixin, PermissionRequiredMixin, DeleteView):
    seccion = "tours"
    permission_required = "tours.delete_tour"
    model = Tour
    template_name = "tour_confirm_delete.html"
    context_object_name = "tour"
    success_url = reverse_lazy("tour_list")

    def form_valid(self, form):
        if self.object.cotizaciones.exists():
            messages.error(
                self.request,
                f"«{self.object.title}» tiene cotizaciones y no se puede eliminar.",
            )
            return redirect("tour_list")
        foto = self.object.foto
        messages.success(self.request, f"Eliminado correctamente\nTour «{self.object.title}»")
        response = super().form_valid(form)
        if foto:
            foto.storage.delete(foto.name)
        return response


# ---------------------------------------------------------------- Destinos

class DestinationListView(StaffRequiredMixin, ListView):
    seccion = "destinos"
    model = Destination
    template_name = "destino_list.html"
    context_object_name = "destinos"

    def get_queryset(self):
        # Con Count, Django ignora el ordering del modelo: se repite para seguir el orden del sitio.
        return super().get_queryset().annotate(num_tours=Count("tours")).order_by("orden", "name")


class DestinationCreateView(StaffRequiredMixin, PermissionRequiredMixin, FotoMixin, SuccessMessageMixin, CreateView):
    seccion = "destinos"
    permission_required = "tours.add_destination"
    model = Destination
    form_class = DestinationForm
    template_name = "destino_form.html"
    success_url = reverse_lazy("destino_list")
    success_message = "Creado correctamente\nDestino «%(name)s»"


class DestinationUpdateView(StaffRequiredMixin, PermissionRequiredMixin, FotoMixin, SuccessMessageMixin, UpdateView):
    seccion = "destinos"
    permission_required = "tours.change_destination"
    model = Destination
    form_class = DestinationForm
    template_name = "destino_form.html"
    success_url = reverse_lazy("destino_list")
    success_message = "Actualizado correctamente\nDestino «%(name)s»"


class DestinationDeleteView(StaffRequiredMixin, PermissionRequiredMixin, DeleteView):
    seccion = "destinos"
    permission_required = "tours.delete_destination"
    model = Destination
    template_name = "destino_confirm_delete.html"
    context_object_name = "destino"
    success_url = reverse_lazy("destino_list")

    def form_valid(self, form):
        # Un destino con tours no se borra (on_delete=PROTECT): primero hay que moverlos.
        if self.object.tours.exists():
            messages.error(self.request, f"«{self.object.name}» tiene tours. Muévelos a otro destino antes de eliminarlo.")
            return redirect("destino_list")
        foto = self.object.foto
        messages.success(self.request, f"Eliminado correctamente\nDestino «{self.object.name}»")
        response = super().form_valid(form)
        if foto:
            foto.storage.delete(foto.name)
        return response


# ---------------------------------------------------------------- Categorías

class CategoriaListView(StaffRequiredMixin, ListView):
    seccion = "categorias"
    model = Categoria
    template_name = "categoria_list.html"
    context_object_name = "categorias"

    def get_queryset(self):
        return super().get_queryset().annotate(num_tours=Count("tours")).order_by("orden", "nombre")


class CategoriaCreateView(StaffRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    seccion = "categorias"
    permission_required = "tours.add_categoria"
    model = Categoria
    form_class = CategoriaForm
    template_name = "categoria_form.html"
    success_url = reverse_lazy("categoria_list")
    success_message = "Creada correctamente\nCategoría «%(nombre)s»"


class CategoriaUpdateView(StaffRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    seccion = "categorias"
    permission_required = "tours.change_categoria"
    model = Categoria
    form_class = CategoriaForm
    template_name = "categoria_form.html"
    success_url = reverse_lazy("categoria_list")
    success_message = "Actualizada correctamente\nCategoría «%(nombre)s»"


class CategoriaDeleteView(StaffRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Borrar una categoría solo la quita de sus tours: los tours no se tocan."""

    seccion = "categorias"
    permission_required = "tours.delete_categoria"
    model = Categoria
    template_name = "categoria_confirm_delete.html"
    context_object_name = "categoria"
    success_url = reverse_lazy("categoria_list")

    def form_valid(self, form):
        messages.success(self.request, f"Eliminada correctamente\nCategoría «{self.object.nombre}»")
        return super().form_valid(form)
