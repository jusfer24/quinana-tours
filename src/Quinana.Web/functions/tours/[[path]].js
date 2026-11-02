// /tours/* (ruta antigua del panel, Django la redirige a /crm/) se atiende en Django (ver cloudflare/django-proxy.js).
import { proxyToDjango } from "../../cloudflare/django-proxy.js";

export const onRequest = proxyToDjango;
