"""Pruebas del panel interno (CRM): acceso, navegación y gestión de cotizaciones.

Ejecutar con:  python manage.py test crm
"""

import re
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from tours.models import ActividadLead, Destination, LeadCotizacion, PagoHito, Tour

from . import services

PASSWORD = "Quinana-2026!"


def enlace_activo(response):
    """Texto del enlace del menú marcado con aria-current="page" (sin el ícono)."""
    html = response.content.decode()
    enlace = re.search(r'aria-current="page">(.*?)</a>', html, re.S).group(1)
    return re.sub(r"<svg.*?</svg>|<[^>]+>", "", enlace, flags=re.S).split()[0]
Estado = LeadCotizacion.EstadoEmbudo


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

    def test_viajero_no_ve_las_cotizaciones(self):
        self.client.force_login(self.viajero)
        self.assertEqual(self.client.get(reverse("lead_list")).status_code, 403)

    def test_personal_ve_el_inicio_con_el_menu(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("crm_inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solicitudes recibidas")
        self.assertContains(response, 'href="%s"' % reverse("tour_list"))
        # La sección activa queda marcada para lectores de pantalla.
        self.assertEqual(enlace_activo(response), "Inicio")

    def test_catalogo_marca_su_seccion(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("tour_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(enlace_activo(response), "Tours")

    def test_raiz_lleva_al_inicio_del_panel(self):
        self.assertRedirects(self.client.get("/"), reverse("crm_inicio"), fetch_redirect_response=False)

    def test_ruta_antigua_de_tours_redirige_al_panel(self):
        self.assertRedirects(self.client.get("/tours/"), "/crm/catalogo/tours/", fetch_redirect_response=False)
        self.assertRedirects(
            self.client.get("/tours/editar/3/"), "/crm/catalogo/tours/editar/3/", fetch_redirect_response=False
        )


class LeadTestCase(TestCase):
    """Datos comunes: un tour, un admin (todos los permisos), un staff sin permisos y una cotización."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="admin", password=PASSWORD, first_name="Camila")
        cls.lector = User.objects.create_user(username="lector", password=PASSWORD, is_staff=True)
        andes, _ = Destination.objects.get_or_create(name="Andes")
        cls.tour = Tour.objects.create(
            title="Quilotoa", destination=andes, duration_days=2,
            description="Laguna del Quilotoa.", price_usd=Decimal("500.00"),
        )

    def setUp(self):
        self.lead = LeadCotizacion.objects.create(
            nombre_cliente="Emily Carter", email_cliente="emily@test.com", tour=self.tour,
            numero_pasajeros=2, fecha_estimada=timezone.localdate() + timedelta(days=60),
        )
        self.client.force_login(self.admin)

    def accion(self, accion, **data):
        return self.client.post(reverse("lead_detail", args=[self.lead.pk]), {"accion": accion, **data})


class LeadServicesTests(LeadTestCase):
    def test_cambiar_estado_deja_rastro_en_el_historial(self):
        services.cambiar_estado(self.lead, Estado.COTIZADA, self.admin)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.estado_embudo, Estado.COTIZADA)
        actividad = self.lead.actividades.get()
        self.assertEqual(actividad.tipo, ActividadLead.Tipo.ESTADO)
        self.assertIn("Nueva → Cotizada", actividad.texto)

    def test_no_se_cierra_con_cambiar_estado(self):
        with self.assertRaises(ValueError):
            services.cambiar_estado(self.lead, Estado.CERRADA, self.admin)

    def test_cerrar_y_reabrir(self):
        services.cerrar(self.lead, LeadCotizacion.ResultadoCierre.PERDIDA, "Precio", self.admin)
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.esta_cerrada)
        self.assertIsNotNone(self.lead.fecha_cierre)
        services.reabrir(self.lead, self.admin)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.estado_embudo, Estado.SEGUIMIENTO)
        self.assertIsNone(self.lead.resultado_cierre)
        self.assertEqual(self.lead.actividades.count(), 2)

    def test_siguiente_estado(self):
        self.assertEqual(services.siguiente_estado(self.lead), Estado.SEGUIMIENTO)
        self.lead.estado_embudo = Estado.NEGOCIACION
        self.assertIsNone(services.siguiente_estado(self.lead))


class LeadListTests(LeadTestCase):
    def test_lista_y_filtros(self):
        LeadCotizacion.objects.create(
            nombre_cliente="Lukas Weber", email_cliente="lukas@test.com", tour=self.tour,
            numero_pasajeros=4, fecha_estimada=timezone.localdate(), responsable=self.admin,
        )
        response = self.client.get(reverse("lead_list"))
        self.assertContains(response, "Emily Carter")
        self.assertContains(response, "Lukas Weber")

        response = self.client.get(reverse("lead_list"), {"responsable": "sin"})
        self.assertContains(response, "Emily Carter")
        self.assertNotContains(response, "Lukas Weber")

        response = self.client.get(reverse("lead_list"), {"q": "lukas"})
        self.assertNotContains(response, "Emily Carter")
        self.assertContains(response, "Lukas Weber")

    def test_embudo_muestra_columnas_y_valor(self):
        response = self.client.get(reverse("lead_embudo"))
        self.assertContains(response, "En negociación")
        self.assertContains(response, "Emily Carter")
        self.assertEqual(response.context["columnas"][0]["valor"], Decimal("1000.00"))

    def test_menu_avisa_las_nuevas(self):
        response = self.client.get(reverse("crm_inicio"))
        self.assertEqual(response.context["cotizaciones_nuevas"], 1)


class LeadCreateTests(LeadTestCase):
    def test_registrar_cotizacion_a_mano(self):
        response = self.client.post(reverse("lead_create"), {
            "nombre_cliente": "Sophie Martin", "email_cliente": "sophie@test.com",
            "telefono": "+33 6 12 34 56 78", "canal_preferido": "WHATSAPP",
            "tour": self.tour.pk, "numero_pasajeros": 2,
            "fecha_estimada": (timezone.localdate() + timedelta(days=30)).isoformat(),
            "origen_lead": "WhatsApp", "mensaje": "Viaje de aniversario", "responsable": self.admin.pk,
        })
        lead = LeadCotizacion.objects.get(email_cliente="sophie@test.com")
        self.assertRedirects(response, reverse("lead_detail", args=[lead.pk]))
        self.assertEqual(lead.contactos.get().telefono, "+33 6 12 34 56 78")
        self.assertTrue(lead.actividades.filter(tipo=ActividadLead.Tipo.CREACION).exists())

    def test_formulario_invalido_no_crea_nada(self):
        response = self.client.post(reverse("lead_create"), {"nombre_cliente": "Sin datos"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LeadCotizacion.objects.count(), 1)


class LeadDetailActionsTests(LeadTestCase):
    def test_ficha_muestra_datos_y_acciones(self):
        response = self.client.get(reverse("lead_detail", args=[self.lead.pk]))
        self.assertContains(response, "Emily Carter")
        self.assertContains(response, "Asignármela")
        self.assertContains(response, "Pasar a En seguimiento")

    def test_asignarme_y_avanzar(self):
        self.accion("asignar", responsable=self.admin.pk)
        self.accion("estado", estado=Estado.SEGUIMIENTO)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.responsable, self.admin)
        self.assertEqual(self.lead.estado_embudo, Estado.SEGUIMIENTO)
        self.assertEqual(self.lead.actividades.count(), 2)

    def test_avanzar_desde_el_embudo_vuelve_al_embudo(self):
        response = self.accion("estado", estado=Estado.SEGUIMIENTO, volver="embudo", filtros="responsable=sin")
        self.assertRedirects(response, reverse("lead_embudo") + "?responsable=sin", fetch_redirect_response=False)

    def test_cerrar_como_perdida_exige_motivo(self):
        response = self.accion("cerrar", resultado="PERDIDA", motivo="")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Indica el motivo", status_code=400)
        self.lead.refresh_from_db()
        self.assertFalse(self.lead.esta_cerrada)

        self.accion("cerrar", resultado="PERDIDA", motivo="Eligió otra operadora")
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.resultado_cierre, "PERDIDA")

    def test_nota_y_pago(self):
        self.accion("nota", texto="  Llamé al cliente  ")
        self.accion(
            "pago", monto="300.00", tipo_pago="ABONO", estado_transaccion="APROBADA",
            pasarela="Transferencia", token_referencia="TRF-1",
        )
        self.assertEqual(self.lead.actividades.get(tipo=ActividadLead.Tipo.NOTA).texto, "Llamé al cliente")
        self.assertEqual(PagoHito.objects.get(lead=self.lead).monto, Decimal("300.00"))
        response = self.client.get(reverse("lead_detail", args=[self.lead.pk]))
        self.assertEqual(response.context["total_aprobado"], Decimal("300.00"))

    def test_accion_desconocida(self):
        self.assertEqual(self.accion("borrar").status_code, 400)

    def test_personal_sin_permisos_ve_pero_no_modifica(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse("lead_detail", args=[self.lead.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Asignármela")
        self.assertEqual(self.accion("estado", estado=Estado.SEGUIMIENTO).status_code, 403)
        self.assertEqual(self.client.get(reverse("lead_create")).status_code, 403)

        self.lector.user_permissions.add(Permission.objects.get(codename="change_leadcotizacion"))
        self.assertEqual(self.accion("estado", estado=Estado.SEGUIMIENTO).status_code, 302)


class SolicitudCotizacionApiTests(TestCase):
    """POST /api/cotizaciones/: formulario "Solicitar cotización" del sitio público."""

    @classmethod
    def setUpTestData(cls):
        andes, _ = Destination.objects.get_or_create(name="Andes")
        cls.tour = Tour.objects.create(
            title="Quilotoa", destination=andes, duration_days=2,
            description="Laguna del Quilotoa.", price_usd=Decimal("500.00"),
        )

    def setUp(self):
        cache.clear()  # el límite de envíos se guarda en la caché

    def datos(self, **cambios):
        return {
            "nombre": "  Emily   Carter ", "email": "Emily@Test.com", "telefono": "+1 415 555 0134",
            "tour": self.tour.pk, "pasajeros": 2,
            "fecha": (timezone.localdate() + timedelta(days=45)).isoformat(),
            "mensaje": "Luna de miel", **cambios,
        }

    def post(self, data):
        return self.client.post(reverse("api_cotizaciones"), data, content_type="application/json")

    def test_crea_la_cotizacion_su_contacto_y_su_historial(self):
        self.assertEqual(self.post(self.datos()).status_code, 201)
        lead = LeadCotizacion.objects.get()
        self.assertEqual(lead.nombre_cliente, "Emily Carter")
        self.assertEqual(lead.email_cliente, "emily@test.com")
        self.assertEqual(lead.estado_embudo, Estado.NUEVA)
        self.assertEqual(lead.origen_lead, "Sitio web")
        self.assertEqual(lead.contactos.get().canal_preferido, "WHATSAPP")
        self.assertEqual(lead.actividades.get().tipo, ActividadLead.Tipo.CREACION)

    def test_valida_los_datos(self):
        response = self.post(self.datos(
            nombre="", email="no-es-correo", tour=999, pasajeros=0,
            fecha=timezone.localdate().isoformat(), telefono="12",
        ))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.json()), {"nombre", "email", "tour", "pasajeros", "fecha", "telefono"}
        )
        self.assertFalse(LeadCotizacion.objects.exists())

    def test_campo_trampa_ignora_a_los_bots(self):
        self.assertEqual(self.post(self.datos(website="http://spam.example")).status_code, 201)
        self.assertFalse(LeadCotizacion.objects.exists())

    def test_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("api_cotizaciones"), self.datos(), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_limita_los_envios_por_ip(self):
        for _ in range(10):
            self.assertEqual(self.post(self.datos()).status_code, 201)
        self.assertEqual(self.post(self.datos()).status_code, 429)


class InicioMetricasTests(LeadTestCase):
    """Indicadores del inicio (crm/metricas.py) con datos controlados."""

    def cerrar(self, nombre, resultado, hace_dias):
        lead = LeadCotizacion.objects.create(
            nombre_cliente=nombre, email_cliente=f"{nombre}@test.com", tour=self.tour,
            numero_pasajeros=2, fecha_estimada=timezone.localdate() + timedelta(days=40),
            # Llegó antes del periodo: solo cuenta su cierre, no su tiempo de respuesta.
            created_at=timezone.now() - timedelta(days=hace_dias + 40),
        )
        services.cerrar(lead, resultado, "" if resultado == "GANADA" else "Precio", self.admin)
        LeadCotizacion.objects.filter(pk=lead.pk).update(fecha_cierre=timezone.now() - timedelta(days=hace_dias))
        return lead

    def test_indicadores_del_periodo(self):
        self.cerrar("ganada", "GANADA", 3)
        self.cerrar("perdida", "PERDIDA", 4)
        self.cerrar("antigua", "GANADA", 60)  # fuera del periodo de 30 días
        # La cotización de setUp se responde 2 horas después de llegar.
        ActividadLead.objects.create(
            lead=self.lead, autor=self.admin, tipo=ActividadLead.Tipo.NOTA, texto="Llamada",
            fecha=self.lead.created_at + timedelta(hours=2),
        )
        response = self.client.get(reverse("crm_inicio"), {"periodo": "30"})
        kpi = response.context["kpi"]
        self.assertEqual(kpi["conversion"]["valor"], 50)  # 1 ganada de 2 cerradas en 30 días
        self.assertEqual(kpi["ganado"]["valor"], "$1 000")  # 500 USD × 2 pax
        self.assertEqual(kpi["respuesta"]["horas"], 2)
        self.assertTrue(kpi["respuesta"]["cumple"])

    def test_avisa_las_nuevas_sin_responsable(self):
        LeadCotizacion.objects.filter(pk=self.lead.pk).update(created_at=timezone.now() - timedelta(days=2))
        response = self.client.get(reverse("crm_inicio"))
        avisos = response.context["avisos"]
        self.assertEqual(avisos[0]["lead"], self.lead)
        self.assertIn("Sin responsable", avisos[0]["motivo"])

    def test_periodo_desconocido_usa_el_inicial(self):
        response = self.client.get(reverse("crm_inicio"), {"periodo": "999"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["periodo"]["clave"], "90")

    def test_coordenadas_del_svg_con_punto_decimal(self):
        # Con el idioma en español, floatformat pondría coma decimal y rompería el SVG.
        response = self.client.get(reverse("crm_inicio"))
        self.assertNotRegex(response.content.decode(), r'(x|y|width|cx|cy)="\d+,\d')

    def test_calendario_marca_la_salida_y_los_dias_de_viaje(self):
        # Tour de 2 días que sale el día 10 del mes siguiente.
        salida = (timezone.localdate().replace(day=1) + timedelta(days=40)).replace(day=10)
        LeadCotizacion.objects.filter(pk=self.lead.pk).update(fecha_estimada=salida)
        services.cerrar(self.lead, "GANADA", "", self.admin)
        response = self.client.get(reverse("crm_inicio"), {"mes": salida.strftime("%Y-%m")})
        dias = {d["fecha"]: d for semana in response.context["viajes"]["semanas"] for d in semana}
        self.assertEqual(dias[salida]["salidas"], 1)
        self.assertEqual(dias[salida]["chips"][0]["texto"], "Emily · 2 pax")
        self.assertEqual(dias[salida + timedelta(days=1)]["en_ruta"], 1)  # segundo día del tour
        self.assertEqual(dias[salida + timedelta(days=2)]["en_ruta"], 0)

    def test_mes_invalido_muestra_el_mes_actual(self):
        response = self.client.get(reverse("crm_inicio"), {"mes": "no-es-fecha"})
        self.assertEqual(response.context["viajes"]["mes"], timezone.localdate().replace(day=1))
