"""Rutas principales del proyecto.

- /login/   Inicio de sesión (vista de autenticación de Django).
- /logout/  Cierre de sesión (solo POST, por seguridad).
- /tours/   CRUD de tours: sección protegida, requiere sesión iniciada.
- /admin/   Panel de administración de Django.
- /api/auth/  API de acceso de los viajeros del sitio público (Astro).
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tour_list", permanent=False)),
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,  # si ya inició sesión, va directo al CRUD
            extra_context={"site_url": settings.FRONTEND_URL},  # botón "Volver al sitio"
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("tours/", include("tours.urls")),
    path("api/auth/", include("accounts.urls")),
]
