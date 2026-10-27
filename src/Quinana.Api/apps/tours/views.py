"""Controladores (C del patrón MVC) del CRUD de tours.

Todas las vistas heredan de LoginRequiredMixin: si el usuario no ha iniciado sesión,
Django lo redirige a LOGIN_URL (/login/) y, tras autenticarse, lo devuelve a la página
que intentaba abrir (parámetro ?next=).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
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


# C - Create (Crear tour)
class TourCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
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
class TourUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
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
class TourDeleteView(LoginRequiredMixin, DeleteView):
    model = Tour
    template_name = "tour_confirm_delete.html"
    context_object_name = "tour"
    success_url = reverse_lazy("tour_list")

    def form_valid(self, form):
        messages.success(self.request, f"Tour «{self.object.title}» eliminado.")
        return super().form_valid(form)
