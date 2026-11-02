// Formulario "Solicitar cotización" (isla React, se hidrata al hacerse visible).
// Valida en el navegador con Zod + React Hook Form y envía a la API de Django
// (POST /api/cotizaciones/), que crea la cotización en el CRM.
// Los textos llegan por props desde src/i18n/ui.ts para servir en español e inglés.
// Los botones "Consultar" de cada tour ([data-cotizar-tour]) preseleccionan su tour aquí.

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ApiError, post } from "../lib/api";
import type { ui } from "../i18n/ui";

type Texts = (typeof ui)["es"]["quote"] | (typeof ui)["en"]["quote"];

interface Props {
	lang: "es" | "en";
	tours: { id: number; title: string }[];
	text: Texts;
}

const MAX_TRAVELERS = 30;

/** Fecha en formato AAAA-MM-DD (hora local), a `days` días de hoy. */
function isoDate(days: number): string {
	const date = new Date();
	date.setDate(date.getDate() + days);
	const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
	return local.toISOString().slice(0, 10);
}

function buildSchema(errors: Texts["errors"]) {
	return z.object({
		name: z.string().trim().min(2, errors.name),
		email: z.email(errors.email),
		phone: z
			.string()
			.trim()
			.refine((value) => !value || (value.match(/\d/g)?.length ?? 0) >= 7, errors.phone),
		tour: z.string().min(1, errors.tour),
		travelers: z
			.number({ error: errors.travelers })
			.int(errors.travelers)
			.min(1, errors.travelers)
			.max(MAX_TRAVELERS, errors.travelers),
		date: z.string().refine((value) => value >= isoDate(1), errors.date),
		message: z.string().max(2000, errors.message),
		website: z.string(), // campo trampa para bots (invisible)
	});
}

type FormValues = z.infer<ReturnType<typeof buildSchema>>;

// Nombre del campo en la API de Django → nombre en este formulario.
const API_FIELDS: Record<string, keyof FormValues> = {
	nombre: "name",
	email: "email",
	telefono: "phone",
	tour: "tour",
	pasajeros: "travelers",
	fecha: "date",
	mensaje: "message",
};

const inputClass =
	"mt-1.5 w-full rounded-lg border border-borde bg-white px-3.5 py-2.5 text-base text-tinta " +
	"placeholder:text-musgo/70 hover:border-selva/50 focus:border-selva focus:ring-2 focus:ring-selva/20 " +
	"focus:outline-none aria-[invalid=true]:border-red-600";

export default function QuoteForm({ lang, tours, text }: Props) {
	const [sent, setSent] = useState<{ name: string; email: string } | null>(null);
	const successRef = useRef<HTMLHeadingElement>(null);
	const {
		register,
		handleSubmit,
		setValue,
		setError,
		reset,
		formState: { errors, isSubmitting },
	} = useForm<FormValues>({
		resolver: zodResolver(buildSchema(text.errors)),
		defaultValues: { name: "", email: "", phone: "", tour: "", travelers: 2, date: "", message: "", website: "" },
	});

	// "Consultar" en una tarjeta de tour: deja ese tour elegido en el formulario.
	useEffect(() => {
		function onClick(event: MouseEvent) {
			const link = (event.target as HTMLElement).closest<HTMLElement>("[data-cotizar-tour]");
			if (link) setValue("tour", link.dataset.cotizarTour ?? "", { shouldValidate: true });
		}
		document.addEventListener("click", onClick);
		return () => document.removeEventListener("click", onClick);
	}, [setValue]);

	useEffect(() => {
		if (sent) successRef.current?.focus();
	}, [sent]);

	async function onSubmit(values: FormValues) {
		try {
			await post("/api/cotizaciones/", {
				nombre: values.name,
				email: values.email,
				telefono: values.phone,
				tour: Number(values.tour),
				pasajeros: values.travelers,
				fecha: values.date,
				mensaje: values.message,
				website: values.website,
			});
			setSent({ name: values.name.split(" ")[0], email: values.email });
			reset();
		} catch (error) {
			const fields = error instanceof ApiError ? Object.keys(error.fields) : [];
			const known = fields.filter((field) => field in API_FIELDS);
			// Errores por campo: se muestran con el texto del idioma de la página.
			for (const field of known) {
				const name = API_FIELDS[field];
				setError(name, { message: text.errors[name as keyof Texts["errors"]] ?? text.errors.generic });
			}
			if (!known.length) {
				const rateLimited = error instanceof ApiError && error.status === 429;
				setError("root", { message: rateLimited ? text.errors.rateLimit : text.errors.generic });
			}
		}
	}

	if (sent) {
		return (
			<div className="rounded-2xl bg-white p-6 text-tinta shadow-2xl sm:p-8" role="status">
				<h3 ref={successRef} tabIndex={-1} className="font-display text-2xl font-extrabold text-selva focus:outline-none">
					{text.successTitle.replace("{name}", sent.name)}
				</h3>
				<p className="mt-3 leading-relaxed text-musgo">{text.successText.replace("{email}", sent.email)}</p>
				<button
					type="button"
					onClick={() => setSent(null)}
					className="mt-6 rounded-full border border-selva px-5 py-2.5 text-sm font-semibold text-selva transition-colors hover:bg-selva hover:text-white"
				>
					{text.again}
				</button>
			</div>
		);
	}

	const fieldError = (name: keyof FormValues) =>
		errors[name] && (
			<p id={`quote-${name}-error`} className="mt-1 text-sm text-red-700">
				{errors[name]?.message}
			</p>
		);
	const a11y = (name: keyof FormValues) => ({
		id: `quote-${name}`,
		"aria-invalid": errors[name] ? true : undefined,
		"aria-describedby": errors[name] ? `quote-${name}-error` : undefined,
	});

	return (
		<form
			onSubmit={handleSubmit(onSubmit)}
			noValidate
			className="rounded-2xl bg-white p-6 text-tinta shadow-2xl sm:p-8"
			aria-labelledby="quote-title"
		>
			<h3 id="quote-title" className="font-display text-2xl font-extrabold text-selva">
				{text.title}
			</h3>

			<div className="mt-5 grid gap-4 sm:grid-cols-2">
				<div className="sm:col-span-2">
					<label htmlFor="quote-name" className="text-sm font-semibold">{text.name}</label>
					<input {...register("name")} {...a11y("name")} type="text" autoComplete="name" className={inputClass} />
					{fieldError("name")}
				</div>

				<div>
					<label htmlFor="quote-email" className="text-sm font-semibold">{text.email}</label>
					<input {...register("email")} {...a11y("email")} type="email" autoComplete="email" className={inputClass} />
					{fieldError("email")}
				</div>

				<div>
					<label htmlFor="quote-phone" className="text-sm font-semibold">{text.phone}</label>
					<input
						{...register("phone")}
						{...a11y("phone")}
						type="tel"
						autoComplete="tel"
						placeholder="+1 415 555 0134"
						className={inputClass}
					/>
					{fieldError("phone") ?? <p className="mt-1 text-xs text-musgo">{text.phoneHint}</p>}
				</div>

				<div className="sm:col-span-2">
					<label htmlFor="quote-tour" className="text-sm font-semibold">{text.tour}</label>
					<select {...register("tour")} {...a11y("tour")} className={`${inputClass} cursor-pointer`} disabled={!tours.length}>
						<option value="">{tours.length ? text.tourPlaceholder : text.noTours}</option>
						{tours.map((tour) => (
							<option key={tour.id} value={String(tour.id)} lang={lang === "es" ? undefined : "es"}>
								{tour.title}
							</option>
						))}
					</select>
					{fieldError("tour")}
				</div>

				<div>
					<label htmlFor="quote-travelers" className="text-sm font-semibold">{text.travelers}</label>
					<input
						{...register("travelers", { valueAsNumber: true })}
						{...a11y("travelers")}
						type="number"
						min={1}
						max={MAX_TRAVELERS}
						inputMode="numeric"
						className={inputClass}
					/>
					{fieldError("travelers")}
				</div>

				<div>
					<label htmlFor="quote-date" className="text-sm font-semibold">{text.date}</label>
					<input {...register("date")} {...a11y("date")} type="date" min={isoDate(1)} className={inputClass} />
					{fieldError("date")}
				</div>

				<div className="sm:col-span-2">
					<label htmlFor="quote-message" className="text-sm font-semibold">{text.message}</label>
					<textarea
						{...register("message")}
						{...a11y("message")}
						rows={3}
						placeholder={text.messagePlaceholder}
						className={`${inputClass} resize-y`}
					/>
					{fieldError("message")}
				</div>

				{/* Campo trampa: oculto para personas y lectores de pantalla; los bots lo rellenan. */}
				<div className="hidden" aria-hidden="true">
					<label htmlFor="quote-website">Website</label>
					<input {...register("website")} id="quote-website" type="text" tabIndex={-1} autoComplete="off" />
				</div>
			</div>

			{errors.root && (
				<p role="alert" className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800">
					{errors.root.message}
				</p>
			)}

			<button
				type="submit"
				disabled={isSubmitting}
				aria-busy={isSubmitting}
				className="mt-6 inline-flex w-full items-center justify-center gap-2.5 rounded-full bg-terracota px-6 py-3.5 font-semibold text-white transition-colors hover:bg-terracota-oscuro active:scale-[0.99] disabled:cursor-progress disabled:opacity-85"
			>
				{isSubmitting && (
					<span
						aria-hidden="true"
						className="size-4 animate-spin rounded-full border-2 border-white border-r-transparent motion-reduce:animate-none"
					/>
				)}
				{isSubmitting ? text.sending : text.submit}
			</button>
			<p className="mt-3 text-center text-xs text-musgo">{text.privacy}</p>
		</form>
	);
}
