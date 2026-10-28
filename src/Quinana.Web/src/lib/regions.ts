// Las cuatro regiones del sitio. `name` coincide con el destino del CRUD de Django
// (ver el comando cargar_catalogo), así los tours toman la foto de su región.
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
		tagline: "Islas encantadas",
		image: galapagos,
		alt: "Dos lobos marinos caminando por la orilla de una playa en la isla Isabela, Galápagos",
		credit: {
			subject: "Lobos marinos, Isabela",
			author: "Charles J. Sharp",
			license: "CC BY-SA 3.0",
			url: "https://commons.wikimedia.org/wiki/File:Gal%C3%A1pagos_sea_lions_Isabela.jpg",
		},
	},
	{
		name: "Andes",
		tagline: "Volcanes y lagunas",
		image: andes,
		alt: "El volcán Cotopaxi nevado entre nubes, sobre el páramo andino",
		credit: {
			subject: "Cotopaxi",
			author: "Bernard Gagnon",
			license: "CC BY-SA 3.0",
			url: "https://commons.wikimedia.org/wiki/File:Cotopaxi_01.jpg",
		},
	},
	{
		name: "Amazonía",
		tagline: "Selva viva",
		image: amazonia,
		alt: "Pasarela de madera entre árboles gigantes hacia un lodge en la Reserva Cuyabeno",
		credit: {
			subject: "Lodge en Cuyabeno",
			author: "Fährtenleser",
			license: "CC0",
			url: "https://commons.wikimedia.org/wiki/File:Lodge_im_Cuyabeno_Wildtier-Reservat.jpg",
		},
	},
	{
		name: "Costa",
		tagline: "Pacífico y ballenas",
		image: costa,
		alt: "Olas del Pacífico rompiendo en la playa Los Frailes, rodeada de acantilados verdes",
		credit: {
			subject: "Playa Los Frailes",
			author: "AnitaAD",
			license: "CC BY-SA 4.0",
			url: "https://commons.wikimedia.org/wiki/File:Playa_Los_Frailes.jpg",
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
