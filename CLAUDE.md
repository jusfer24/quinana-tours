# Project Context

Este proyecto es un MVP para un catálogo web de turismo receptivo en Ecuador, dirigido a público extranjero (Norteamérica y Europa).

El objetivo principal es la captación de leads mediante un flujo de "Venta Consultiva" (sin pasarela de pago inicial) y una optimización extrema para SEO (Core Web Vitals).

## Architecture & Tech Stack

- **Frontend:** Astro (Static Site Generation) para velocidad extrema y SEO.
- **Interactividad:** React (Islands Architecture) exclusivamente para formularios de contacto y calculadoras.
- **Estilos:** Tailwind CSS.
- **Backend / CRM:** Django + Django REST Framework.
- **Base de Datos:** PostgreSQL.
- **Infraestructura:** Cloudflare Pages (Frontend estático) y servidor VPS en Hetzner (Backend y BD en contenedores Docker).

## Development Rules & AI Guidelines

1. **Rendimiento primero:** Mantén la generación estática (SSG) de Astro siempre que sea posible. No conviertas componentes estáticos a React a menos que requieran estado en el cliente.
2. **Formularios y Leads:** Todos los llamados a la acción (CTAs) son para "Solicitar Cotización" o "Consultar Disponibilidad". Los datos capturados en React deben enviarse a la API de Django.
3. **Manejo de Imágenes:** Utiliza siempre el componente `<Image/>` nativo de Astro con formatos modernos (WebP/AVIF) para asegurar tiempos de carga bajos.
4. **Backend:** El backend de Django funciona como una API RESTful y un CRM interno para operadoras. Todo el despliegue local de la base de datos debe gestionarse con Docker Compose.

## Development Commands

### Frontend (Astro)

## When starting the dev server, use background mode:
```bash
astro dev --background
astro dev stop
astro dev status
astro dev logs
```


## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

### Frontend & UI
- [Astro:](https://docs.astro.build)
- [React:](https://react.dev)
- [Tailwind CSS:](https://tailwindcss.com/docs)

### Gestión de Formularios y Validación (React)
- [React Hook Form:](https://react-hook-form.com/get-started)
- [Zod (Validación de esquemas):](https://zod.dev)

### Backend & API
- [Django:](https://docs.djangoproject.com)
- [Django REST Framework (DRF):](https://www.django-rest-framework.org)
- [Django Allauth (Autenticación futura):](https://docs.allauth.org)

### Base de Datos
- [PostgreSQL:](https://www.postgresql.org/docs)

### Infraestructura & Despliegue
- [Docker:](https://docs.docker.com)
- [Docker Compose:](https://docs.docker.com/compose)
- [Cloudflare Pages (Hosting Frontend):](https://developers.cloudflare.com/pages)
- [Hetzner Cloud (Hosting VPS Backend):](https://docs.hetzner.com/cloud)

### Analítica & SEO (Integraciones)
- [Google Tag Manager:](https://developers.google.com/tag-platform/tag-manager)
- [Google Analytics 4 (GA4):](https://developers.google.com/analytics)