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

    def test_registro_crea_usuario_sin_iniciar_sesion(self):
        response = self.post(
            "/api/auth/register/",
            {"full_name": "Bob", "email": "Bob@Test.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(email="bob@test.com").exists())
        self.assertIsNone(self.client.get("/api/auth/me/").json()["user"])

        # Con la cuenta creada, el viajero ya puede iniciar sesión.
        response = self.post("/api/auth/login/", {"email": "bob@test.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)

    def test_registro_rechaza_correo_repetido(self):
        response = self.post(
            "/api/auth/register/",
            {"full_name": "Ana", "email": "ANA@test.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_registro_rechaza_contrasena_debil(self):
        response = self.post(
            "/api/auth/register/",
            {"full_name": "Bob", "email": "bob@test.com", "password": "12345678"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())

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

    def test_viajero_ve_el_catalogo_pero_no_puede_modificarlo(self):
        self.client.force_login(self.user)
        response = self.client.get("/tours/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Nuevo tour")
        self.assertEqual(self.client.get("/tours/nuevo/").status_code, 403)
