"""Controladores (C del patrón MVC) del CRUD de tours.

Sin sesión, todas las vistas redirigen a LOGIN_URL (/login/) y, tras autenticarse,
devuelven al usuario a la página que intentaba abrir (?next=).

- Listar: cualquier usuario con sesión (también los viajeros del sitio público).
  La plantilla solo muestra "Nuevo tour", "Editar" y "Eliminar" a quien tiene permiso.
- Crear, editar y eliminar: PermissionRequiredMixin; sin el permiso del modelo, 403.
  Provisional hasta que se definan los roles.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import TourForm
from .models import Tour


# R - Read (Listar tours)
class TourListView(LoginRequiredMixin, ListView):
    model = Tour
    template_name = "tour_list.html"
    context_object_name = "tours"
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().select_related("destination")


# C - Create (Crear tour)
class TourCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
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
class TourUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
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
class TourDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "tours.delete_tour"
    model = Tour
    template_name = "tour_confirm_delete.html"
    context_object_name = "tour"
    success_url = reverse_lazy("tour_list")

    def form_valid(self, form):
        messages.success(self.request, f"Tour «{self.object.title}» eliminado.")
        return super().form_valid(form)
