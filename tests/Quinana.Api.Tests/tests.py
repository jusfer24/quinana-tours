"""Pruebas del login y de la protección del CRUD de tours.

Ejecutar con:  python manage.py test
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Tour

USERNAME = "operador"
PASSWORD = "Quinana-2026!"


class AuthTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(username=USERNAME, password=PASSWORD)
        cls.tour = Tour.objects.create(
            title="Galápagos Island Hopping",
            destination="Galápagos",
            duration="5 días / 4 noches",
            description="Recorrido por las islas.",
            price_usd=Decimal("1500.00"),
        )

    def protected_urls(self):
        return [
            reverse("tour_list"),
            reverse("tour_create"),
            reverse("tour_update", args=[self.tour.pk]),
            reverse("tour_delete", args=[self.tour.pk]),
        ]


class ProtectedUrlsTests(AuthTestCase):
    def test_protected_urls_redirect_to_login_without_session(self):
        for url in self.protected_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_anonymous_post_cannot_create_or_delete(self):
        self.client.post(reverse("tour_create"), {"title": "Intruso"})
        self.client.post(reverse("tour_delete", args=[self.tour.pk]))
        self.assertEqual(Tour.objects.count(), 1)

    def test_root_redirects_to_login_without_session(self):
        response = self.client.get("/", follow=True)
        self.assertEqual(response.request["PATH_INFO"], reverse("login"))


class LoginTests(AuthTestCase):
    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión")

    def test_wrong_password_shows_error_and_does_not_log_in(self):
        response = self.client.post(
            reverse("login"), {"username": USERNAME, "password": "incorrecta"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alert--error")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_valid_login_redirects_to_crud(self):
        response = self.client.post(
            reverse("login"), {"username": USERNAME, "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("tour_list"))

    def test_login_returns_to_the_requested_page(self):
        target = reverse("tour_create")
        response = self.client.post(
            f"{reverse('login')}?next={target}",
            {"username": USERNAME, "password": PASSWORD, "next": target},
        )
        self.assertRedirects(response, target)

    def test_logout_blocks_access_again(self):
        self.client.login(username=USERNAME, password=PASSWORD)
        self.client.post(reverse("logout"))
        response = self.client.get(reverse("tour_list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('tour_list')}")


class CrudWithSessionTests(AuthTestCase):
    def setUp(self):
        self.client.login(username=USERNAME, password=PASSWORD)

    def test_list(self):
        response = self.client.get(reverse("tour_list"))
        self.assertContains(response, "Galápagos Island Hopping")

    def test_create(self):
        response = self.client.post(
            reverse("tour_create"),
            {
                "title": "Quilotoa Trek",
                "destination": "Andes",
                "duration": "1 día",
                "description": "Caminata al cráter.",
                "price_usd": "120.00",
            },
        )
        self.assertRedirects(response, reverse("tour_list"))
        self.assertTrue(Tour.objects.filter(title="Quilotoa Trek").exists())

    def test_update(self):
        response = self.client.post(
            reverse("tour_update", args=[self.tour.pk]),
            {
                "title": "Galápagos Premium",
                "destination": "Galápagos",
                "duration": "6 días",
                "description": "Actualizado.",
                "price_usd": "1800.00",
            },
        )
        self.assertRedirects(response, reverse("tour_list"))
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.title, "Galápagos Premium")

    def test_delete(self):
        response = self.client.post(reverse("tour_delete", args=[self.tour.pk]))
        self.assertRedirects(response, reverse("tour_list"))
        self.assertFalse(Tour.objects.exists())
