import os

from django.conf import settings
from django.contrib.staticfiles import finders

from tours.models import LeadCotizacion


def version_css():
    """Versión de app.css (fecha de modificación) para la URL del <link>: app.css?v=...

    Django no manda Cache-Control para este archivo, así que sin la versión el navegador
    reutiliza una copia vieja y el panel se ve sin los estilos nuevos tras cada cambio.
    """
    path = finders.find("css/app.css")
    try:
        return int(os.path.getmtime(path))
    except (TypeError, OSError):
        return 0


def panel(request):
    """Datos comunes del panel: enlace al sitio público, versión del CSS y aviso de cotizaciones nuevas."""
    context = {"frontend_url": settings.FRONTEND_URL, "css_version": version_css()}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_staff:
        context["cotizaciones_nuevas"] = LeadCotizacion.objects.filter(
            estado_embudo=LeadCotizacion.EstadoEmbudo.NUEVA
        ).count()
    return context
