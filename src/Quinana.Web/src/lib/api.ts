// Cliente de la API de Django. Usa la cookie de sesión (credentials: "include") y el
// token CSRF que Django exige en toda petición que cambia estado.
//
// La URL se configura con PUBLIC_API_URL en src/Quinana.Web/.env. En local debe usar
// "localhost" (no 127.0.0.1), igual que el sitio Astro, para que el navegador envíe
// la cookie de sesión. En Cloudflare Pages va vacío: el navegador llama a /api/ del mismo
// sitio y functions/ lo reenvía a Django (ver cloudflare/django-proxy.js).

export const API_URL = import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000";

/** Error de la API. `fields` trae los errores por campo que devuelve Django ({ email: ["..."] }). */
export class ApiError extends Error {
	constructor(
		message: string,
		readonly fields: Record<string, string[]> = {},
	) {
		super(message);
	}
}

const NETWORK_ERROR = "No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.";
const GENERIC_ERROR = "Algo salió mal. Inténtalo de nuevo en unos minutos.";

async function request(path: string, init: RequestInit = {}): Promise<Response> {
	try {
		return await fetch(`${API_URL}${path}`, { ...init, credentials: "include" });
	} catch {
		throw new ApiError(NETWORK_ERROR);
	}
}

// Se pide un token nuevo en cada envío: Django lo cambia al iniciar sesión.
async function csrfToken(): Promise<string> {
	const response = await request("/api/auth/csrf/");
	if (!response.ok) throw new ApiError(GENERIC_ERROR);
	return (await response.json()).csrfToken;
}

export async function post<T = unknown>(path: string, body: unknown): Promise<T> {
	const response = await request(path, {
		method: "POST",
		headers: { "Content-Type": "application/json", "X-CSRFToken": await csrfToken() },
		body: JSON.stringify(body),
	});
	const data = response.status === 204 ? null : await response.json().catch(() => null);
	if (response.ok) return data as T;

	if (response.status === 400 && data && typeof data === "object") {
		const { detail, non_field_errors, ...fields } = data;
		const message = detail ?? non_field_errors?.[0] ?? "Revisa los datos del formulario.";
		throw new ApiError(message, fields);
	}
	throw new ApiError(GENERIC_ERROR);
}
