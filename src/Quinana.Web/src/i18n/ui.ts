// Textos del sitio público en español (raíz /) e inglés (/en/).
// Los tours vienen del CRUD de Django y solo existen en español: en /en/ se muestran tal cual.

export const languages = { es: "Español", en: "English" } as const;
export type Lang = keyof typeof languages;

/** Ruta de inicio de cada idioma. */
export const homePath: Record<Lang, string> = { es: "/", en: "/en/" };

export const ui = {
	es: {
		meta: {
			title: "Quinana Tours | Tours a tu medida por Ecuador",
			description:
				"Tours personalizados por Galápagos, Andes, Amazonía y Costa de Ecuador. Solicita tu cotización y un experto local armará tu itinerario.",
		},
		nav: {
			destinations: "Destinos",
			tours: "Tours",
			how: "Cómo funciona",
			login: "Iniciar sesión",
			quote: "Solicitar cotización",
			menu: "Menú",
			close: "Cerrar",
			switchTo: "English",
		},
		logoTagline: "Ecuador a tu medida",
		hero: {
			imageAlt: "Laguna del Quilotoa, un lago de cráter turquesa rodeado de montañas en los Andes de Ecuador",
			title: "Cuatro mundos en un país pequeño.",
			text: "Galápagos, los Andes, la Amazonía y la Costa caben en un mismo viaje. Un experto local arma tu ruta y te envía la cotización sin costo.",
			primary: "Solicitar cotización",
			secondary: "Ver tours",
		},
		profile: {
			title: "Del mar a 5.897 metros",
			text: "De oeste a este, Ecuador pasa del Pacífico a los glaciares de los Andes y baja a la selva. Elige por dónde empezar.",
			label: "Perfil de altitud de Ecuador, de Galápagos a la Amazonía",
			facts: {
				Galápagos: "A unos 1.000 km de la costa",
				Costa: "Nivel del mar",
				Andes: "Cotopaxi, 5.897 m",
				Amazonía: "Selva baja",
			},
			tours: (n: number) => (n === 1 ? "1 tour" : `${n} tours`),
			from: "desde",
			noTours: "Tours a pedido",
		},
		tours: {
			title: "Tours para empezar",
			text: "Son puntos de partida: ajustamos fechas, hoteles y ritmo a tu viaje.",
			count: "tours",
			clear: "Quitar filtros",
			destination: "Destino",
			anyDestination: "Todos",
			duration: "Duración",
			anyDuration: "Cualquiera",
			upTo3: "Hasta 3 días",
			from4to5: "4 a 5 días",
			from6: "6 días o más",
			budget: "Presupuesto por persona",
			anyBudget: "Cualquiera",
			upTo700: "Hasta $700",
			from700to1500: "$700 a $1.500",
			over1500: "Más de $1.500",
			days: (n: number) => (n === 1 ? "1 día" : `${n} días`),
			perPerson: "USD por persona",
			ask: "Consultar disponibilidad",
			empty: "Pronto publicaremos nuevos tours. Mientras tanto, cuéntanos tu viaje y te armamos uno a tu medida.",
			noMatch: "Ningún tour coincide con esos filtros, pero podemos armar uno a tu medida.",
			noMatchCta: "Solicitar cotización",
		},
		how: {
			title: "Cómo funciona",
			text: "Sin carrito de compras ni pagos en línea. Hablas con una persona desde el primer mensaje.",
			steps: [
				{ title: "Cuéntanos tu viaje", text: "Fechas, cuántos viajan y qué te gustaría vivir. Sin compromiso." },
				{ title: "Recibe tu itinerario", text: "Un experto local arma una propuesta con precios y la ajusta contigo." },
				{ title: "Confirma y viaja", text: "Pagas solo cuando la propuesta te convence. Te acompañamos durante el viaje." },
			],
		},
		tips: {
			title: "Antes de viajar",
			items: [
				{
					title: "La mejor época",
					text: "Galápagos se visita todo el año: de diciembre a mayo el agua es más cálida y de junio a noviembre hay más vida marina. Las ballenas llegan a la Costa de junio a septiembre.",
				},
				{
					title: "La altura",
					text: "Quito está a 2.850 metros. Toma el primer día con calma, bebe mucha agua y deja las caminatas exigentes para después.",
				},
				{
					title: "Qué llevar",
					text: "Ropa en capas para los Andes, manga larga ligera y repelente para la Amazonía, y protector solar para Galápagos y la Costa.",
				},
			],
		},
		cta: {
			imageAlt: "El volcán Cotopaxi cubierto de nieve y nubes sobre el páramo",
			title: "Tu viaje empieza con una conversación",
			text: "Crea tu cuenta para guardar tus tours favoritos y recibir una propuesta personalizada de un experto local.",
			register: "Crear una cuenta",
			login: "Ya tengo cuenta",
		},
		footer: {
			about: "Turismo receptivo en Ecuador. Te acercamos a Galápagos, los Andes, la Amazonía y la Costa con viajes armados a tu medida.",
			explore: "Explorar",
			destinations: "Destinos",
			account: "Tu cuenta",
			login: "Iniciar sesión",
			register: "Crear una cuenta",
			photos: "Fotos de Wikimedia Commons:",
			quilotoa: "Laguna del Quilotoa: Omri D. Cohen (Unsplash).",
		},
	},
	en: {
		meta: {
			title: "Quinana Tours | Tailor-made tours in Ecuador",
			description:
				"Private, tailor-made tours to the Galápagos, the Andes, the Amazon and the coast of Ecuador. Request a quote and a local expert will plan your itinerary.",
		},
		nav: {
			destinations: "Destinations",
			tours: "Tours",
			how: "How it works",
			login: "Sign in",
			quote: "Request a quote",
			menu: "Menu",
			close: "Close",
			switchTo: "Español",
		},
		logoTagline: "Ecuador, your way",
		hero: {
			imageAlt: "Quilotoa Lagoon, a turquoise crater lake surrounded by mountains in the Ecuadorian Andes",
			title: "Four worlds in one small country.",
			text: "The Galápagos, the Andes, the Amazon and the Pacific coast fit into a single trip. A local expert plans your route and sends you a free quote.",
			primary: "Request a quote",
			secondary: "See tours",
		},
		profile: {
			title: "From sea level to 5,897 meters",
			text: "Going west to east, Ecuador climbs from the Pacific to the glaciers of the Andes, then drops into the rainforest. Pick where to start.",
			label: "Elevation profile of Ecuador, from the Galápagos to the Amazon",
			facts: {
				Galápagos: "About 1,000 km offshore",
				Costa: "Sea level",
				Andes: "Cotopaxi, 5,897 m",
				Amazonía: "Lowland rainforest",
			},
			tours: (n: number) => (n === 1 ? "1 tour" : `${n} tours`),
			from: "from",
			noTours: "Tours on request",
		},
		tours: {
			title: "Tours to start from",
			text: "Think of them as starting points: we adapt dates, hotels and pace to your trip.",
			count: "tours",
			clear: "Clear filters",
			destination: "Destination",
			anyDestination: "All",
			duration: "Length",
			anyDuration: "Any",
			upTo3: "Up to 3 days",
			from4to5: "4 to 5 days",
			from6: "6 days or more",
			budget: "Budget per person",
			anyBudget: "Any",
			upTo700: "Up to $700",
			from700to1500: "$700 to $1,500",
			over1500: "Over $1,500",
			days: (n: number) => (n === 1 ? "1 day" : `${n} days`),
			perPerson: "USD per person",
			ask: "Check availability",
			empty: "New tours are coming soon. In the meantime, tell us about your trip and we will plan one for you.",
			noMatch: "No tours match those filters, but we can plan one around them.",
			noMatchCta: "Request a quote",
		},
		how: {
			title: "How it works",
			text: "No shopping cart and no online payments. You talk to a real person from the first message.",
			steps: [
				{ title: "Tell us about your trip", text: "Dates, who is coming and what you want to experience. No commitment." },
				{ title: "Get your itinerary", text: "A local expert sends a priced proposal and fine-tunes it with you." },
				{ title: "Confirm and travel", text: "You pay only once the proposal feels right. We stay in touch during the trip." },
			],
		},
		tips: {
			title: "Before you go",
			items: [
				{
					title: "When to visit",
					text: "The Galápagos are a year-round destination: the water is warmer from December to May, and marine life peaks from June to November. Humpback whales reach the coast from June to September.",
				},
				{
					title: "Altitude",
					text: "Quito sits at 2,850 meters. Take your first day slowly, drink plenty of water and save the demanding hikes for later.",
				},
				{
					title: "What to pack",
					text: "Layers for the Andes, light long sleeves and insect repellent for the Amazon, and sunscreen for the Galápagos and the coast.",
				},
			],
		},
		cta: {
			imageAlt: "Snow-capped Cotopaxi volcano rising above clouds and the páramo",
			title: "Your trip starts with a conversation",
			text: "Create an account to save the tours you like and receive a personal proposal from a local expert.",
			register: "Create an account",
			login: "I have an account",
		},
		footer: {
			about: "Inbound travel in Ecuador. We take you to the Galápagos, the Andes, the Amazon and the coast on trips built around you.",
			explore: "Explore",
			destinations: "Destinations",
			account: "Your account",
			login: "Sign in",
			register: "Create an account",
			photos: "Photos from Wikimedia Commons:",
			quilotoa: "Quilotoa Lagoon: Omri D. Cohen (Unsplash).",
		},
	},
} as const;

export function t(lang: Lang) {
	return ui[lang];
}

/** Idioma de la página actual según la URL (Astro.currentLocale). */
export function langFrom(locale: string | undefined): Lang {
	return locale === "en" ? "en" : "es";
}
