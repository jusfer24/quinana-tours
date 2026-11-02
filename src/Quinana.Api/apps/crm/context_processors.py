from django.conf import settings


def panel(request):
    """Datos comunes del panel: enlace "Ver sitio público" del menú lateral."""
    return {"frontend_url": settings.FRONTEND_URL}
