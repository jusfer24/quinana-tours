// Catálogo público que expone Django en /api/tours/. Astro lo lee al generar la página
// (en `astro dev`, en cada visita; en `astro build`, una vez). Si la API no responde,
// la página se genera igual con la lista vacía.

import { API_URL } from "./api";

export interface Tour {
	id: number;
	title: string;
	destination: string;
	duration_days: number;
	duration_label: string;
	description: string;
	price_usd: string;
}

export async function fetchTours(): Promise<Tour[]> {
	try {
		const response = await fetch(`${API_URL}/api/tours/`);
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		return await response.json();
	} catch (error) {
		console.warn(`[tours] No se pudo leer el catálogo de ${API_URL}: ${error}`);
		return [];
	}
}

const usd = new Intl.NumberFormat("en-US", {
	style: "currency",
	currency: "USD",
	maximumFractionDigits: 0,
});

export function formatPrice(price: string): string {
	return usd.format(Number(price));
}
