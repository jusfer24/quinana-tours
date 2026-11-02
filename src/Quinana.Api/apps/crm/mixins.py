"""Control de acceso del panel interno (CRM).

Solo entra el personal (is_staff). Sin sesión se redirige al "Acceso del equipo" del
sitio público (LOGIN_URL); un viajero con sesión recibe 403 (plantilla 403.html).
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    # Sección del menú lateral que se marca como activa (ver crm/base_crm.html).
    seccion = ""

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["seccion"] = self.seccion
        return context
