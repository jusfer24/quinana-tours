<h1 align="center">Quinana Tours</h1>

<p align="center">
  Catálogo web de tours por Ecuador donde los viajeros internacionales<br>
  descubren experiencias y solicitan cotizaciones personalizadas.
</p>

## Índice

- [Descripción](#descripción)
- [Estado del proyecto](#estado-del-proyecto)
- [Funcionalidades](#funcionalidades)
- [Arquitectura MVC](#arquitectura-mvc)
- [Requisitos](#requisitos)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Pruebas](#pruebas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Tecnologías](#tecnologías)
- [Cómo contribuir](#cómo-contribuir)
- [Contribuidores](#contribuidores)
- [Licencia](#licencia)

## Descripción

Quinana Tours es un catálogo web de tours por Ecuador (Andes, Amazonía y Galápagos) dirigido a viajeros extranjeros.

Los paquetes de turismo receptivo son de alto valor (de USD 1.500 a 10.000 o más) y el viajero quiere hablar con una persona antes de pagar. Por eso el sitio no usa un carrito de compras: cada llamado a la acción es «Solicitar cotización» o «Consultar disponibilidad», y el equipo de ventas cierra la venta de forma personalizada.

El repositorio contiene dos partes:

- **Aplicación Django (MVC):** panel interno donde el equipo inicia sesión y gestiona el catálogo de tours (crear, listar, editar y eliminar). Todas sus URLs están protegidas por autenticación.
- **Sitio Astro:** frontend público para los viajeros, generado como sitio estático para lograr la máxima velocidad y un buen posicionamiento en buscadores.

## Estado del proyecto

En desarrollo (MVP).

| Módulo | Estado |
|---|---|
| CRUD de tours con patrón MVC (Django) | Completado |
| Inicio y cierre de sesión con rutas protegidas (Django) | Completado |
| Página de acceso del sitio público (Astro): diseño, validación y términos | Interfaz completada |
| Catálogo público de tours y formulario «Solicitar cotización» | Pendiente |
| API REST y CRM de leads | Pendiente |

## Funcionalidades

### Aplicación Django

- **Inicio de sesión** con usuario y contraseña mediante el sistema de autenticación de Django. Las contraseñas se guardan cifradas y los errores se muestran en español.
- **Rutas protegidas:** sin sesión iniciada, cualquier URL del CRUD (`/tours/`, `/tours/nuevo/`, `/tours/editar/<id>/`, `/tours/eliminar/<id>/`) redirige a `/login/`. Después de iniciar sesión, el usuario vuelve a la página que intentaba abrir.
- **Cierre de sesión** mediante una petición POST con protección CSRF. Tras cerrar sesión, las rutas vuelven a quedar bloqueadas.
- **CRUD de tours:** crear, listar, editar y eliminar tours (título, destino, duración, descripción y precio), con mensajes de confirmación.
- **Diseño responsive** con media queries para móvil, tableta y escritorio.

### Sitio Astro

- Página de acceso con pantalla de bienvenida, pestañas de inicio de sesión y registro, recuperación de contraseña y validación en español.
- Términos y política de privacidad redactados con base en la Ley Orgánica de Protección de Datos Personales y la Ley Orgánica de Defensa del Consumidor del Ecuador.

## Arquitectura MVC

Django implementa el patrón MVC con su propia nomenclatura (MTV: Model, Template, View):

| Capa MVC | En Django | Archivo |
|---|---|---|
| Modelo | Modelo | [`tours/models.py`](tours/models.py): clase `Tour` y su tabla en la base de datos |
| Vista | Plantilla | [`tours/Vistas/`](tours/Vistas/) y [`templates/`](templates/): HTML que ve el usuario |
| Controlador | Vista | [`tours/views.py`](tours/views.py): recibe la petición, usa el modelo y elige la plantilla |
| Enrutamiento | URLconf | [`config/urls.py`](config/urls.py) y [`tours/urls.py`](tours/urls.py) |

La protección de las rutas se aplica en el controlador: cada vista hereda de `LoginRequiredMixin`, y la configuración de [`config/settings.py`](config/settings.py) (`LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`) define adónde se envía al usuario.

## Requisitos

- [Python](https://www.python.org/) 3.12 o superior
- [Node.js](https://nodejs.org/) 22.12 o superior (solo para el sitio Astro)
- Git

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/jusfer24/Web-Page_Quinana-Tours.git
cd Web-Page_Quinana-Tours
```

### 2. Aplicación Django (login y CRUD)

1. Crea y activa un entorno virtual:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

2. Instala las dependencias y crea la base de datos:

   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   ```

3. Crea un usuario para iniciar sesión:

   ```bash
   python manage.py createsuperuser
   ```

4. Inicia el servidor:

   ```bash
   python manage.py runserver
   ```

5. Abre <http://127.0.0.1:8000/>. Al no tener sesión, el sitio te redirige a `/login/`; después de iniciar sesión verás el CRUD en `/tours/`.

### 3. Sitio Astro (opcional)

```bash
npm install
npx astro dev --background
```

Abre <http://localhost:4321/login>. Para detener el servidor usa `npx astro dev stop`.

> Usa `npm install` en lugar de `npm ci`: el archivo `package-lock.json` todavía no está sincronizado con `package.json`.

## Pruebas

La aplicación Django incluye pruebas automáticas que verifican el login y la protección de las rutas:

```bash
python manage.py test
```

| Prueba | Qué comprueba |
|---|---|
| `ProtectedUrlsTests` | Ninguna URL del CRUD es accesible sin sesión; un usuario anónimo no puede crear ni eliminar tours |
| `LoginTests` | Credenciales correctas e incorrectas, regreso a la página solicitada y bloqueo tras cerrar sesión |
| `CrudWithSessionTests` | Listar, crear, editar y eliminar con sesión iniciada |

## Estructura del proyecto

```text
Web-Page_Quinana-Tours/
├── config/                  # Configuración del proyecto Django
│   ├── settings.py              # Ajustes, incluida la configuración de login
│   └── urls.py                  # Rutas principales: /login/, /logout/, /tours/
├── tours/                   # Aplicación del CRUD de tours
│   ├── models.py                # Modelo (M)
│   ├── views.py                 # Controladores (C), protegidos con LoginRequiredMixin
│   ├── forms.py                 # Formulario de tours
│   ├── urls.py                  # Rutas del CRUD
│   ├── tests.py                 # Pruebas de login y CRUD
│   └── Vistas/                  # Plantillas del CRUD (V)
├── templates/               # Plantillas compartidas (V)
│   ├── base.html                # Estructura común y barra de usuario
│   └── registration/login.html  # Página de inicio de sesión
├── static/                  # CSS e imágenes de la aplicación Django
├── manage.py
├── requirements.txt         # Dependencias de Python
├── src/                     # Sitio Astro (frontend público)
│   ├── components/              # Formularios de acceso y términos
│   ├── pages/                   # Rutas del sitio (index.astro, login.astro)
│   ├── scripts/                 # Validación en el cliente
│   └── styles/                  # Estilos
├── public/                  # Archivos estáticos del sitio Astro
└── package.json             # Dependencias de Node.js
```

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend, login y CRUD | [Django](https://www.djangoproject.com) 5.2 |
| Base de datos (desarrollo) | SQLite |
| Frontend público | [Astro](https://astro.build) con generación estática |
| Interactividad | [React](https://react.dev) (islas), solo para formularios y calculadoras |
| Estilos | CSS con media queries y [Tailwind CSS](https://tailwindcss.com) |
| Base de datos (producción, planificado) | [PostgreSQL](https://www.postgresql.org) |
| Infraestructura (planificado) | [Cloudflare Pages](https://pages.cloudflare.com) para el frontend y un VPS en [Hetzner](https://www.hetzner.com) con Docker para el backend |

## Cómo contribuir

1. Crea una rama a partir de `develop` con el prefijo que corresponda:

   | Prefijo | Uso | Ejemplo |
   |---|---|---|
   | `feature/` | Nueva funcionalidad | `feature/catalogo-tours` |
   | `fix/` | Corrección de errores | `fix/validacion-correo` |
   | `docs/` | Documentación | `docs/guia-despliegue` |
   | `chore/` | Mantenimiento y configuración | `chore/actualizar-dependencias` |

2. Escribe los mensajes de commit con el formato [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

   ```text
   feat(auth): protege las rutas del CRUD con inicio de sesión
   fix(tours): corrige la columna de acciones de la tabla
   docs: documenta la instalación de Django
   ```

3. Ejecuta `python manage.py test` antes de subir tus cambios.

4. Sube tu rama y abre un Pull Request hacia `develop`. Cuando `develop` esté estable, se integra en `main`, que siempre contiene código listo para producción.

## Contribuidores

| [<img src="https://github.com/jusfer24.png" width="100" alt="Foto de perfil de Justin Basantes"><br><sub>Justin Basantes</sub>](https://github.com/jusfer24) | [<img src="https://github.com/KamiNSoria.png" width="100" alt="Foto de perfil de KamiNSoria"><br><sub>KamiNSoria</sub>](https://github.com/KamiNSoria) |
| :---: | :---: |

## Licencia

Licencia pendiente de definir. Mientras tanto, todos los derechos están reservados por sus autores.

La fotografía de la Laguna del Quilotoa es de [Omri D. Cohen en Unsplash](https://unsplash.com/photos/MzeSloMrFTY) y se usa bajo la [Licencia Unsplash](https://unsplash.com/license).
