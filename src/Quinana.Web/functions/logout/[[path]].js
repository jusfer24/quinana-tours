// /logout/* se atiende en Django (ver cloudflare/django-proxy.js).
import { proxyToDjango } from "../../cloudflare/django-proxy.js";

export const onRequest = proxyToDjango;
