"""Pruebas de la API pública del catálogo (/api/tours/) y del acceso al CRUD.

Ejecutar con:  python manage.py test tours
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Destination, Tour


class PublicTourApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        andes, _ = Destination.objects.get_or_create(name="Andes")  # la migración 0002 ya lo crea
        Tour.objects.create(
            title="Quilotoa Adventure",
            destination=andes,
            duration_days=1,
            description="Laguna del Quilotoa en un día.",
            price_usd=Decimal("690.00"),
        )

    def test_lista_tours_sin_sesion(self):
        response = self.client.get("/api/tours/")
        self.assertEqual(response.status_code, 200)
        tour = response.json()[0]
        self.assertEqual(tour["title"], "Quilotoa Adventure")
        self.assertEqual(tour["destination"], "Andes")
        self.assertEqual(tour["duration_label"], "1 día")
        self.assertEqual(tour["price_usd"], "690.00")

    def test_no_permite_modificar_el_catalogo(self):
        response = self.client.post("/api/tours/", {"title": "X"}, content_type="application/json")
        self.assertEqual(response.status_code, 405)


class CrmLoginRedirectTestCase(TestCase):
    """Django no tiene login propio: el CRM envía al "Acceso del equipo" del sitio Astro."""

    def test_sin_sesion_redirige_al_acceso_del_equipo(self):
        response = self.client.get(reverse("tour_list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(settings.FRONTEND_URL.rstrip("/") + "/login"))
        self.assertTrue(response["Location"].endswith("#equipo"))

    def test_no_existe_login_de_django(self):
        self.assertEqual(self.client.get("/login/").status_code, 404)

    def test_cerrar_sesion_vuelve_al_acceso_del_equipo(self):
        user = get_user_model().objects.create_user(username="operador", password="Quinana-2026!", is_staff=True)
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, settings.LOGOUT_REDIRECT_URL, fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("tour_list")).status_code, 302)
