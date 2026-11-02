"""Pruebas del panel interno (CRM): acceso solo para el personal y navegación.

Ejecutar con:  python manage.py test crm
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

PASSWORD = "Quinana-2026!"


class PanelAccessTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user(username="operador", password=PASSWORD, is_staff=True)
        cls.viajero = User.objects.create_user(username="ana@test.com", email="ana@test.com", password=PASSWORD)

    def test_sin_sesion_redirige_al_acceso_del_equipo(self):
        response = self.client.get(reverse("crm_inicio"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(settings.FRONTEND_URL.rstrip("/") + "/login"))

    def test_viajero_recibe_pagina_403_amable(self):
        self.client.force_login(self.viajero)
        response = self.client.get(reverse("crm_inicio"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "solo para el equipo", status_code=403)

    def test_personal_ve_el_inicio_con_el_menu(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("crm_inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cotizaciones abiertas")
        self.assertContains(response, 'href="%s"' % reverse("tour_list"))
        # La sección activa queda marcada para lectores de pantalla.
        self.assertContains(response, 'aria-current="page">Inicio')

    def test_catalogo_marca_su_seccion(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("tour_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-current="page">Tours')

    def test_raiz_lleva_al_inicio_del_panel(self):
        self.assertRedirects(self.client.get("/"), reverse("crm_inicio"), fetch_redirect_response=False)

    def test_ruta_antigua_de_tours_redirige_al_panel(self):
        self.assertRedirects(self.client.get("/tours/"), "/crm/catalogo/tours/", fetch_redirect_response=False)
        self.assertRedirects(
            self.client.get("/tours/editar/3/"), "/crm/catalogo/tours/editar/3/", fetch_redirect_response=False
        )
