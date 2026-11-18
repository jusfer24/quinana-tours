"""Rutas principales del proyecto.

- /logout/  Cierre de sesión (solo POST, por seguridad).
- /crm/     Panel interno del equipo (CRM): inicio y catálogo de tours en
            /crm/catalogo/tours/. Solo personal (is_staff); sin sesión envía al
            "Acceso del equipo" del sitio público (LOGIN_URL).
- /tours/   Ruta antigua del CRUD: redirige a /crm/catalogo/tours/.
- /admin/   Panel de administración de Django.
- /api/auth/  API de acceso de los viajeros del sitio público (Astro).
- /api/tours/, /api/destinos/ y /api/categorias/  Catálogo público de solo lectura para el sitio Astro.
- /api/cotizaciones/ Formulario "Solicitar cotización" del sitio público (crea un lead en el CRM).
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from crm.api import SolicitudCotizacionView
from tours.api import PublicCategoriaListView, PublicDestinationListView, PublicTourListView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="crm_inicio", permanent=False)),
    path("admin/", admin.site.urls),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("crm/", include("crm.urls")),
    re_path(r"^tours/(?P<resto>.*)$", RedirectView.as_view(url="/crm/catalogo/tours/%(resto)s")),
    path("api/auth/", include("accounts.urls")),
    path("api/tours/", PublicTourListView.as_view(), name="api_tours"),
    path("api/destinos/", PublicDestinationListView.as_view(), name="api_destinos"),
    path("api/categorias/", PublicCategoriaListView.as_view(), name="api_categorias"),
    path("api/cotizaciones/", SolicitudCotizacionView.as_view(), name="api_cotizaciones"),
]

# En local Django sirve las fotos subidas desde el CRM (/media/). En producción no: ver MEDIA_ROOT.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
