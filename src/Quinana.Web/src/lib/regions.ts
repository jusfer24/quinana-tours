// Las cuatro regiones del sitio, de oeste a este. `name` coincide con el destino del CRUD
// de Django (ver el comando cargar_catalogo), así los tours toman la foto de su región.
// `label`, `tagline` y `alt` van en los dos idiomas del sitio (es / en).
//
// Fotos de Wikimedia Commons. Las CC BY-SA exigen dar crédito: se muestra en el pie.

import amazonia from "../assets/destinos/amazonia.jpg";
import andes from "../assets/destinos/andes.jpg";
import costa from "../assets/destinos/costa.jpg";
import galapagos from "../assets/destinos/galapagos.jpg";

export interface Credit {
	subject: string;
	author: string;
	license: string;
	url: string;
}

export const regions = [
	{
		name: "Galápagos",
		label: { es: "Galápagos", en: "Galápagos" },
		tagline: { es: "Islas encantadas", en: "The Enchanted Isles" },
		image: galapagos,
		alt: {
			es: "Dos lobos marinos caminando por la orilla de una playa en la isla Isabela, Galápagos",
			en: "Two sea lions walking along the shore of a beach on Isabela Island, Galápagos",
		},
		credit: {
			subject: "Lobos marinos, Isabela",
			author: "Charles J. Sharp",
			license: "CC BY-SA 3.0",
			url: "https://commons.wikimedia.org/wiki/File:Gal%C3%A1pagos_sea_lions_Isabela.jpg",
		},
	},
	{
		name: "Costa",
		label: { es: "Costa", en: "Coast" },
		tagline: { es: "Pacífico y ballenas", en: "Pacific beaches and whales" },
		image: costa,
		alt: {
			es: "Olas del Pacífico rompiendo en la playa Los Frailes, rodeada de acantilados verdes",
			en: "Pacific waves breaking on Los Frailes beach, framed by green cliffs",
		},
		credit: {
			subject: "Playa Los Frailes",
			author: "AnitaAD",
			license: "CC BY-SA 4.0",
			url: "https://commons.wikimedia.org/wiki/File:Playa_Los_Frailes.jpg",
		},
	},
	{
		name: "Andes",
		label: { es: "Andes", en: "Andes" },
		tagline: { es: "Volcanes y lagunas", en: "Volcanoes and crater lakes" },
		image: andes,
		alt: {
			es: "El volcán Cotopaxi nevado entre nubes, sobre el páramo andino",
			en: "Snow-capped Cotopaxi volcano among clouds, above the Andean páramo",
		},
		credit: {
			subject: "Cotopaxi",
			author: "Bernard Gagnon",
			license: "CC BY-SA 3.0",
			url: "https://commons.wikimedia.org/wiki/File:Cotopaxi_01.jpg",
		},
	},
	{
		name: "Amazonía",
		label: { es: "Amazonía", en: "Amazon" },
		tagline: { es: "Selva viva", en: "Living rainforest" },
		image: amazonia,
		alt: {
			es: "Pasarela de madera entre árboles gigantes hacia un lodge en la Reserva Cuyabeno",
			en: "Wooden boardwalk between giant trees leading to a lodge in the Cuyabeno Reserve",
		},
		credit: {
			subject: "Lodge en Cuyabeno",
			author: "Fährtenleser",
			license: "CC0",
			url: "https://commons.wikimedia.org/wiki/File:Lodge_im_Cuyabeno_Wildtier-Reservat.jpg",
		},
	},
] as const;

export const bannerCredit: Credit = {
	subject: "Cotopaxi",
	author: "Bernard Gagnon",
	license: "CC BY-SA 3.0",
	url: "https://commons.wikimedia.org/wiki/File:Cotopaxi_02.jpg",
};

export function regionFor(destination: string) {
	return regions.find((region) => region.name === destination);
}
