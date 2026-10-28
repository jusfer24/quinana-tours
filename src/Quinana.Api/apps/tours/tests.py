"""Pruebas de la API pública del catálogo (/api/tours/).

Ejecutar con:  python manage.py test tours
"""

from decimal import Decimal

from django.test import TestCase

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
