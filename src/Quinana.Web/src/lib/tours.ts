// Catálogo público que expone Django en /api/tours/, /api/destinos/ y /api/categorias/.
// Todo se edita en el CRM.
// Astro lo lee al generar la página (en `astro dev`, en cada visita; en `astro build`, una
// vez). Si la API no responde, la página se genera igual con las listas vacías.
//
// CATALOG_API_URL (solo al compilar) permite leer el catálogo de una URL distinta a la que
// usa el navegador: en Cloudflare el navegador llama a /api/ del mismo sitio (PUBLIC_API_URL
// vacío) y el build, que no tiene ese proxy, lee directo de Render.

import type { Lang } from "../i18n/ui";
import { API_URL as BROWSER_API_URL } from "./api";

const API_URL = import.meta.env.CATALOG_API_URL || BROWSER_API_URL;

export interface Tour {
	id: number;
	title: string;
	destination: string;
	duration_days: number;
	duration_label: string;
	description: string;
	price_usd: string;
	/** Foto propia del tour (URL absoluta) o null si usa la de su destino. */
	foto: string | null;
	foto_alt: string;
	/** Slugs de sus categorías (tipos de viaje). */
	categorias: string[];
}

export interface Categoria {
	id: number;
	slug: string;
	nombre: string;
	nombre_en: string;
	/** Trazo SVG (24×24, lineal) del ícono elegido en el CRM, o "" si no tiene. */
	icono_svg: string;
}

export interface Credit {
	tema: string;
	autor: string;
	licencia: string;
	url: string;
}

export interface Destino {
	id: number;
	name: string;
	name_en: string;
	frase: string;
	frase_en: string;
	foto: string | null;
	foto_alt: string;
	foto_alt_en: string;
	credito: Credit | null;
}

async function fetchList<T>(path: string): Promise<T[]> {
	try {
		const response = await fetch(`${API_URL}${path}`);
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		return await response.json();
	} catch (error) {
		console.warn(`[catálogo] No se pudo leer ${path} de ${API_URL}: ${error}`);
		return [];
	}
}

export function fetchTours(): Promise<Tour[]> {
	return fetchList<Tour>("/api/tours/");
}

// La portada y el pie de página piden los destinos: en el build se leen una sola vez.
// En `astro dev` se vuelven a leer en cada visita para ver al instante lo editado en el CRM.
let destinos: Promise<Destino[]> | undefined;

export function fetchDestinos(): Promise<Destino[]> {
	if (import.meta.env.DEV || !destinos) destinos = fetchList<Destino>("/api/destinos/");
	return destinos;
}

export function fetchCategorias(): Promise<Categoria[]> {
	return fetchList<Categoria>("/api/categorias/");
}

/** Nombre de la categoría en el idioma de la página (el español si falta el inglés). */
export function categoriaLabel(categoria: Categoria, lang: Lang): string {
	return (lang === "en" && categoria.nombre_en) || categoria.nombre;
}

/** Nombre, frase y descripción de la foto en el idioma de la página (el español si falta el inglés). */
export function destinoText(destino: Destino, lang: Lang) {
	const en = lang === "en";
	return {
		label: (en && destino.name_en) || destino.name,
		tagline: (en && destino.frase_en) || destino.frase,
		alt: (en && destino.foto_alt_en) || destino.foto_alt,
	};
}

const usd = new Intl.NumberFormat("en-US", {
	style: "currency",
	currency: "USD",
	maximumFractionDigits: 0,
});

export function formatPrice(price: string): string {
	return usd.format(Number(price));
}
