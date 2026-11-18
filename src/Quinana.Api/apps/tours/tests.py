"""Pruebas de la API pública del catálogo (/api/tours/, /api/destinos/) y de su edición en el CRM.

Ejecutar con:  python manage.py test tours
"""

import io
import shutil
import tempfile
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Categoria, Destination, LeadCotizacion, Tour

MEDIA_DE_PRUEBA = tempfile.mkdtemp(prefix="quinana-media-")


def tearDownModule():
    shutil.rmtree(MEDIA_DE_PRUEBA, ignore_errors=True)


def foto(nombre="foto.jpg", formato="JPEG"):
    """Una imagen real y diminuta, como la que subiría el equipo."""
    contenido = io.BytesIO()
    Image.new("RGB", (8, 6), (27, 133, 82)).save(contenido, formato)
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type=f"image/{formato.lower()}")


def crear_tour(destino, **datos):
    valores = {
        "title": "Quilotoa Adventure",
        "destination": destino,
        "duration_days": 1,
        "description": "Laguna del Quilotoa en un día.",
        "price_usd": Decimal("690.00"),
        **datos,
    }
    return Tour.objects.create(**valores)


class PublicTourApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        andes, _ = Destination.objects.get_or_create(name="Andes")  # la migración 0002 ya lo crea
        crear_tour(andes)

    def test_lista_tours_sin_sesion(self):
        response = self.client.get("/api/tours/")
        self.assertEqual(response.status_code, 200)
        tour = response.json()[0]
        self.assertEqual(tour["title"], "Quilotoa Adventure")
        self.assertEqual(tour["destination"], "Andes")
        self.assertEqual(tour["duration_label"], "1 día")
        self.assertEqual(tour["price_usd"], "690.00")
        self.assertIsNone(tour["foto"])  # sin foto propia: el sitio usa la de su destino
        self.assertEqual(tour["categorias"], [])

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


class PublicDestinationApiTestCase(TestCase):
    """La migración 0006 pasa a la base de datos los textos que el sitio tenía fijos."""

    def test_lista_destinos_en_orden_y_con_sus_textos(self):
        response = self.client.get("/api/destinos/")
        self.assertEqual(response.status_code, 200)
        destinos = response.json()
        self.assertEqual([d["name"] for d in destinos], ["Galápagos", "Costa", "Andes", "Amazonía"])
        costa = destinos[1]
        self.assertEqual(costa["name_en"], "Coast")
        self.assertEqual(costa["frase"], "Pacífico y ballenas")
        self.assertEqual(costa["credito"]["autor"], "AnitaAD")
        self.assertIsNone(costa["foto"])  # las fotos se suben con cargar_catalogo o desde el CRM

    def test_destino_sin_credito(self):
        Destination.objects.create(name="Cuenca", orden=9)
        cuenca = self.client.get("/api/destinos/").json()[-1]
        self.assertEqual(cuenca["name"], "Cuenca")
        self.assertIsNone(cuenca["credito"])

    def test_no_permite_modificar(self):
        self.assertEqual(self.client.post("/api/destinos/", {"name": "X"}).status_code, 405)


@override_settings(MEDIA_ROOT=MEDIA_DE_PRUEBA)
class CatalogoEnElCrmTestCase(TestCase):
    """Lo que se edita en el CRM es lo que entrega la API al sitio público."""

    @classmethod
    def setUpTestData(cls):
        cls.andes = Destination.objects.get(name="Andes")
        cls.tour = crear_tour(cls.andes)
        User = get_user_model()
        cls.editor = User.objects.create_user(username="editor", password="x", is_staff=True)
        cls.editor.user_permissions.add(
            *Permission.objects.filter(
                codename__in=["change_tour", "delete_tour", "add_destination", "change_destination", "delete_destination"]
            )
        )
        cls.lector = User.objects.create_user(username="lector", password="x", is_staff=True)

    def setUp(self):
        self.client.force_login(self.editor)

    def editar_tour(self, **datos):
        valores = {
            "title": self.tour.title,
            "destination": self.andes.pk,
            "duration_days": 1,
            "description": self.tour.description,
            "price_usd": "690.00",
            "foto_alt": "",
            **datos,
        }
        return self.client.post(reverse("tour_update", args=[self.tour.pk]), valores)

    def test_lista_muestra_la_tarjeta_con_la_foto_del_destino(self):
        response = self.client.get(reverse("tour_list"))
        self.assertContains(response, "Quilotoa Adventure")
        self.assertContains(response, "Foto del destino")
        self.assertContains(response, reverse("destino_list"))  # «Destinos» activo en el menú

    def test_subir_foto_del_tour_llega_a_la_api(self):
        response = self.editar_tour(foto=foto(), foto_alt="Laguna turquesa en el cráter")
        self.assertRedirects(response, reverse("tour_list"))
        tour = self.client.get("/api/tours/").json()[0]
        self.assertTrue(tour["foto"].startswith("http://testserver/media/tours/"))
        self.assertEqual(tour["foto_alt"], "Laguna turquesa en el cráter")

    def test_foto_sin_descripcion_no_se_guarda(self):
        response = self.editar_tour(foto=foto())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "foto_alt", "Describe la foto: la leen los lectores de pantalla y Google.")
        self.tour.refresh_from_db()
        self.assertFalse(self.tour.foto)

    def test_rechaza_archivos_que_no_son_fotos(self):
        archivo = SimpleUploadedFile("itinerario.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.editar_tour(foto=archivo, foto_alt="x")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("foto"))

    def test_reemplazar_o_quitar_la_foto_borra_el_archivo_anterior(self):
        self.editar_tour(foto=foto("primera.jpg"), foto_alt="Primera")
        self.tour.refresh_from_db()
        primera = self.tour.foto.name
        self.editar_tour(foto=foto("segunda.png", "PNG"), foto_alt="Segunda")
        self.tour.refresh_from_db()
        self.assertFalse(self.tour.foto.storage.exists(primera))
        segunda = self.tour.foto.name

        self.editar_tour(**{"foto-clear": "on"})
        self.tour.refresh_from_db()
        self.assertFalse(self.tour.foto)
        self.assertFalse(self.tour.foto.storage.exists(segunda))

    def test_editar_destino_cambia_lo_que_ve_el_sitio(self):
        response = self.client.post(
            reverse("destino_update", args=[self.andes.pk]),
            {
                "name": "Andes", "name_en": "Andes", "frase": "Volcanes, lagunas y páramo", "frase_en": "Volcanoes",
                "foto": foto(), "foto_alt": "Cotopaxi", "foto_alt_en": "Cotopaxi",
                "credito_tema": "", "credito_autor": "", "credito_licencia": "", "credito_url": "", "orden": 3,
            },
        )
        self.assertRedirects(response, reverse("destino_list"))
        andes = next(d for d in self.client.get("/api/destinos/").json() if d["name"] == "Andes")
        self.assertEqual(andes["frase"], "Volcanes, lagunas y páramo")
        self.assertTrue(andes["foto"].startswith("http://testserver/media/destinos/"))
        self.assertIsNone(andes["credito"])

    def test_lista_de_destinos_en_el_orden_del_sitio(self):
        destinos = list(self.client.get(reverse("destino_list")).context["destinos"])
        self.assertEqual([d.name for d in destinos], ["Galápagos", "Costa", "Andes", "Amazonía"])

    def test_cambiar_la_foto_del_destino_borra_el_credito_de_la_anterior(self):
        costa = Destination.objects.get(name="Costa")
        self.assertEqual(costa.credito_autor, "AnitaAD")  # foto inicial de Wikimedia (migración 0006)
        datos = {"name": "Costa", "name_en": "Coast", "frase": "Pacífico", "frase_en": "Pacific",
                 "foto_alt": "Playa", "foto_alt_en": "Beach", "orden": 2}

        self.client.post(reverse("destino_update", args=[costa.pk]), datos)  # sin tocar la foto
        costa.refresh_from_db()
        self.assertEqual(costa.credito_autor, "AnitaAD")

        self.client.post(reverse("destino_update", args=[costa.pk]), {**datos, "foto": foto()})
        costa.refresh_from_db()
        self.assertEqual((costa.credito_autor, costa.credito_url), ("", ""))
        self.assertNotContains(self.client.get(reverse("destino_update", args=[costa.pk])), "Crédito de la foto")

    def test_nombre_de_destino_repetido(self):
        response = self.client.post(reverse("destino_create"), {"name": "andes", "orden": 0})
        self.assertFormError(response.context["form"], "name", "Ya existe un destino con ese nombre.")

    def test_no_se_elimina_un_destino_con_tours(self):
        response = self.client.post(reverse("destino_delete", args=[self.andes.pk]))
        self.assertRedirects(response, reverse("destino_list"))
        self.assertTrue(Destination.objects.filter(pk=self.andes.pk).exists())

    def test_no_se_elimina_un_tour_con_cotizaciones(self):
        LeadCotizacion.objects.create(
            email_cliente="ana@example.com", nombre_cliente="Ana", numero_pasajeros=2,
            fecha_estimada="2027-01-10", tour=self.tour,
        )
        response = self.client.post(reverse("tour_delete", args=[self.tour.pk]))
        self.assertRedirects(response, reverse("tour_list"))
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())

    def test_sin_permiso_no_edita_destinos(self):
        self.client.force_login(self.lector)
        self.assertEqual(self.client.get(reverse("destino_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("destino_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("destino_update", args=[self.andes.pk])).status_code, 403)

    def test_cargar_catalogo_no_pisa_lo_editado_en_el_crm(self):
        Destination.objects.filter(pk=self.andes.pk).update(frase="Editada en el CRM")
        Tour.objects.filter(pk=self.tour.pk).update(price_usd=Decimal("999.00"))
        Tour.objects.create(
            title="Laguna del Quilotoa y Cotopaxi", destination=self.andes, duration_days=3,
            description="Editada en el CRM.", price_usd=Decimal("123.00"),
        )
        call_command("cargar_catalogo", stdout=io.StringIO())

        self.andes.refresh_from_db()
        self.assertEqual(self.andes.frase, "Editada en el CRM")
        self.assertTrue(self.andes.foto)  # la foto vacía sí se completa
        self.assertEqual(Tour.objects.get(title="Laguna del Quilotoa y Cotopaxi").price_usd, Decimal("123.00"))
        self.assertEqual(Tour.objects.get(pk=self.tour.pk).price_usd, Decimal("999.00"))


@override_settings(MEDIA_ROOT=MEDIA_DE_PRUEBA)
class CategoriasTestCase(TestCase):
    """Tipos de viaje: varios por tour, editables en el CRM y con slug estable para el filtro."""

    @classmethod
    def setUpTestData(cls):
        cls.andes = Destination.objects.get(name="Andes")
        cls.tour = crear_tour(cls.andes)
        cls.editor = get_user_model().objects.create_user(username="editor", password="x", is_staff=True)
        cls.editor.user_permissions.add(
            *Permission.objects.filter(codename__in=["change_tour", "add_categoria", "change_categoria", "delete_categoria"])
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def test_la_migracion_crea_las_categorias_iniciales(self):
        response = self.client.get("/api/categorias/")
        self.assertEqual([c["slug"] for c in response.json()], ["aventura", "naturaleza", "cultura", "playa"])
        self.assertEqual(response.json()[1]["nombre_en"], "Nature & wildlife")

    def test_un_tour_con_varias_categorias(self):
        aventura = Categoria.objects.get(slug="aventura")
        naturaleza = Categoria.objects.get(slug="naturaleza")
        response = self.client.post(reverse("tour_update", args=[self.tour.pk]), {
            "title": self.tour.title, "destination": self.andes.pk, "duration_days": 1,
            "description": self.tour.description, "price_usd": "690.00", "foto_alt": "",
            "categorias": [aventura.pk, naturaleza.pk],
        })
        self.assertRedirects(response, reverse("tour_list"))
        self.assertEqual(self.client.get("/api/tours/").json()[0]["categorias"], ["aventura", "naturaleza"])
        self.assertContains(self.client.get(reverse("tour_list")), "Naturaleza y fauna")

    def test_categorias_iniciales_con_su_icono(self):
        playa = self.client.get("/api/categorias/").json()[3]
        self.assertEqual(playa["icono"], "ola")
        self.assertIn("<path", playa["icono_svg"])

    def test_elegir_icono(self):
        cultura = Categoria.objects.get(slug="cultura")
        response = self.client.post(reverse("categoria_update", args=[cultura.pk]),
                                    {"nombre": "Cultura", "nombre_en": "Culture", "icono": "camara", "orden": 3})
        self.assertRedirects(response, reverse("categoria_list"))
        cultura.refresh_from_db()
        self.assertEqual(cultura.icono, "camara")
        self.assertContains(self.client.get(reverse("categoria_update", args=[cultura.pk])), 'value="camara" id="id_icono_')

    def test_icono_que_no_existe(self):
        response = self.client.post(reverse("categoria_create"), {"nombre": "Ciclismo", "icono": "<script>", "orden": 0})
        self.assertFormError(response.context["form"], "icono", "Elige un ícono de la lista.")

    def test_crear_categoria_genera_el_slug(self):
        response = self.client.post(reverse("categoria_create"), {"nombre": "Gastronomía", "nombre_en": "Food", "orden": 5})
        self.assertRedirects(response, reverse("categoria_list"))
        self.assertTrue(Categoria.objects.filter(slug="gastronomia", nombre_en="Food").exists())

    def test_renombrar_no_cambia_el_slug(self):
        playa = Categoria.objects.get(slug="playa")
        self.client.post(reverse("categoria_update", args=[playa.pk]), {"nombre": "Playa y sol", "nombre_en": "Beach", "orden": 4})
        playa.refresh_from_db()
        self.assertEqual((playa.nombre, playa.slug), ("Playa y sol", "playa"))

    def test_nombre_repetido(self):
        response = self.client.post(reverse("categoria_create"), {"nombre": "aventura", "orden": 0})
        self.assertFormError(response.context["form"], "nombre", "Ya existe una categoría con ese nombre.")

    def test_eliminar_categoria_no_borra_sus_tours(self):
        cultura = Categoria.objects.get(slug="cultura")
        self.tour.categorias.add(cultura)
        self.client.post(reverse("categoria_delete", args=[cultura.pk]))
        self.assertFalse(Categoria.objects.filter(pk=cultura.pk).exists())
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())

    def test_cargar_catalogo_asigna_categorias_a_los_tours_de_ejemplo(self):
        call_command("cargar_catalogo", stdout=io.StringIO())
        quito = Tour.objects.get(title="Quito colonial y Mitad del Mundo")
        self.assertEqual([c.slug for c in quito.categorias.all()], ["cultura"])
