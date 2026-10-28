// Reenvía peticiones del sitio (quinana-tours.pages.dev) a la API de Django en Render.
//
// Así el navegador ve un solo dominio: las cookies de sesión y CSRF de Django quedan como
// cookies propias del sitio y no las bloquean los navegadores que rechazan cookies de
// terceros (Safari, Brave, Chrome en incógnito). Lo usan los archivos de functions/.
// La URL de Django se puede cambiar con la variable DJANGO_URL del proyecto de Pages.

const DEFAULT_DJANGO_URL = "https://quinana-api.onrender.com";

export async function proxyToDjango({ request, env }) {
	const djangoUrl = (env.DJANGO_URL || DEFAULT_DJANGO_URL).replace(/\/$/, "");
	const url = new URL(request.url);
	const headers = new Headers(request.headers);
	headers.delete("Host"); // Render enruta por el host de Django, no el del sitio

	const response = await fetch(`${djangoUrl}${url.pathname}${url.search}`, {
		method: request.method,
		headers,
		body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
		// Las redirecciones de Django (p. ej. al login) las sigue el navegador, no el proxy.
		redirect: "manual",
	});

	// Si Django responde con una URL absoluta propia, se cambia por la del sitio.
	const proxied = new Response(response.body, response);
	const location = proxied.headers.get("Location");
	if (location?.startsWith(djangoUrl)) {
		proxied.headers.set("Location", url.origin + location.slice(djangoUrl.length));
	}
	return proxied;
}
