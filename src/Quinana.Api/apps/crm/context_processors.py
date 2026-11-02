from django.conf import settings

from tours.models import LeadCotizacion


def panel(request):
    """Datos comunes del panel: enlace al sitio público y aviso de cotizaciones nuevas."""
    context = {"frontend_url": settings.FRONTEND_URL}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_staff:
        context["cotizaciones_nuevas"] = LeadCotizacion.objects.filter(
            estado_embudo=LeadCotizacion.EstadoEmbudo.NUEVA
        ).count()
    return context
