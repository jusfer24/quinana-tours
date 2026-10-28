"""Controladores (C del patrón MVC) del CRUD de tours.

Todas las vistas heredan de PermissionRequiredMixin: sin sesión, Django redirige a
LOGIN_URL (/login/) y, tras autenticarse, devuelve al usuario a la página que intentaba
abrir (?next=). Con sesión pero sin el permiso del modelo, responde 403.
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import TourForm
from .models import Tour


# R - Read (Listar tours)
class TourListView(PermissionRequiredMixin, ListView):
    permission_required = "tours.view_tour"
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
