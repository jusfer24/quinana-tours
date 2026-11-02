"""Rutas principales del proyecto.

- /logout/  Cierre de sesión (solo POST, por seguridad).
- /tours/   CRUD de tours: sección protegida, requiere sesión iniciada. Sin sesión
            envía al "Acceso del equipo" del sitio público (LOGIN_URL).
- /admin/   Panel de administración de Django.
- /api/auth/  API de acceso de los viajeros del sitio público (Astro).
- /api/tours/ Catálogo público de solo lectura para el sitio Astro.
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from tours.api import PublicTourListView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tour_list", permanent=False)),
    path("admin/", admin.site.urls),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("tours/", include("tours.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/tours/", PublicTourListView.as_view(), name="api_tours"),
]
