"""Pruebas de la API de acceso de viajeros (/api/auth/).

Ejecutar con:  python manage.py test accounts
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

PASSWORD = "Viaje-Ecuador-2026"


class AuthApiTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ana@test.com", email="ana@test.com", password=PASSWORD, first_name="Ana"
        )

    def post(self, url, data):
        return self.client.post(url, data, content_type="application/json")

    def test_login_ok_ignora_mayusculas_del_correo(self):
        response = self.post("/api/auth/login/", {"email": "ANA@test.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["email"], "ana@test.com")

    def test_login_con_contrasena_incorrecta(self):
        response = self.post("/api/auth/login/", {"email": "ana@test.com", "password": "otra-clave-1"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Correo o contraseña incorrectos.")

    def test_logout_cierra_la_sesion(self):
        self.client.force_login(self.user)
        self.assertEqual(self.post("/api/auth/logout/", {}).status_code, 204)
        self.assertIsNone(self.client.get("/api/auth/me/").json()["user"])

    def test_login_exige_token_csrf(self):
        client = self.client_class(enforce_csrf_checks=True)
        response = client.post(
            "/api/auth/login/",
            {"email": "ana@test.com", "password": PASSWORD},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_viajero_no_puede_entrar_al_crud_de_tours(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/tours/").status_code, 403)
