"""Controladores (C del patrón MVC) del CRUD de tours.

Forman parte del panel interno (/crm/catalogo/tours/). Sin sesión, todas las vistas
redirigen a LOGIN_URL: el "Acceso del equipo" del sitio público (/login#equipo).

- Listar: solo el personal (StaffRequiredMixin, is_staff); un viajero recibe 403.
  La plantilla solo muestra "Nuevo tour", "Editar" y "Eliminar" a quien tiene permiso.
- Crear, editar y eliminar: además, PermissionRequiredMixin; sin el permiso del modelo, 403.
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from crm.mixins import StaffRequiredMixin

from .forms import TourForm
from .models import Tour


# R - Read (Listar tours)
class TourListView(StaffRequiredMixin, ListView):
    seccion = "tours"
    model = Tour
    template_name = "tour_list.html"
    context_object_name = "tours"
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("destination")


# C - Create (Crear tour)
class TourCreateView(StaffRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    seccion = "tours"
    permission_required = "tours.add_tour"
    model = Tour
    form_class = TourForm
    template_name = "tour_form.html"
    success_url = reverse_lazy("tour_list")
    success_message = "Tour «%(title)s» creado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Crear tour"
        return context


# U - Update (Actualizar tour)
class TourUpdateView(StaffRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    seccion = "tours"
    permission_required = "tours.change_tour"
    model = Tour
    form_class = TourForm
    template_name = "tour_form.html"
    success_url = reverse_lazy("tour_list")
    success_message = "Tour «%(title)s» actualizado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Actualizar tour"
        return context


# D - Delete (Eliminar tour)
class TourDeleteView(StaffRequiredMixin, PermissionRequiredMixin, DeleteView):
    seccion = "tours"
    permission_required = "tours.delete_tour"
    model = Tour
    template_name = "tour_confirm_delete.html"
    context_object_name = "tour"
    success_url = reverse_lazy("tour_list")

    def form_valid(self, form):
        messages.success(self.request, f"Tour «{self.object.title}» eliminado.")
        return super().form_valid(form)
