// Lógica de los formularios de acceso: validación en el cliente, botones
// "Mostrar contraseña" y el cuadro de términos y privacidad.
// Cada campo muestra su error en el elemento con id `${input.id}-error`.

import { ApiError, post } from "./api";

type Field = HTMLInputElement;

const NOT_AVAILABLE = "Esta función aún no está disponible. Inténtalo más tarde.";

function messageFor(input: Field): string {
	const v = input.validity;
	if (v.valueMissing) return input.dataset.requiredMsg ?? "Este campo es obligatorio.";
	if (v.typeMismatch) return "Ingresa un correo electrónico válido.";
	if (v.tooShort) return `Debe tener al menos ${input.minLength} caracteres.`;
	if (input.dataset.match) {
		const other = document.getElementById(input.dataset.match) as Field | null;
		if (other && input.value !== other.value) return "Las contraseñas no coinciden.";
	}
	return "";
}

function validate(input: Field): boolean {
	const message = messageFor(input);
	const error = document.getElementById(`${input.id}-error`);
	if (error) error.textContent = message;
	input.setAttribute("aria-invalid", String(Boolean(message)));
	return !message;
}

function fieldsIn(root: ParentNode): Field[] {
	return [...root.querySelectorAll<Field>("input[required], input[data-match]")];
}

/** Valida los campos y enfoca el primero con error. Devuelve true si todos son válidos. */
function validateAll(fields: Field[]): boolean {
	const results = fields.map(validate);
	const firstInvalid = fields[results.indexOf(false)];
	firstInvalid?.focus();
	return !firstInvalid;
}

function watchFields(fields: Field[]): void {
	for (const input of fields) {
		if (input.type === "checkbox") {
			input.addEventListener("change", () => validate(input));
			continue;
		}
		// Al salir del campo solo se valida si el usuario ya escribió algo; así no aparecen
		// errores por solo pasar por un campo (o cambiar de pestaña). El envío valida todo.
		let touched = false;
		input.addEventListener("input", () => {
			touched = true;
			if (input.getAttribute("aria-invalid") === "true") validate(input);
		});
		input.addEventListener("blur", () => {
			if (touched) validate(input);
		});
	}
}

// Envío de cada formulario a la API de Django. Sin entrada = la función aún no existe.
type Submit = (data: FormData) => Promise<unknown>;
const SUBMITS: Record<string, Submit> = {
	"login-form": (data) =>
		post("/api/auth/login/", {
			email: data.get("email"),
			password: data.get("password"),
			remember: data.has("remember"),
		}),
};

// Adónde va el viajero tras iniciar sesión.
const AFTER_LOGIN_URL = "/";

/** Muestra los errores por campo que devolvió la API bajo cada input (por su atributo name). */
function showFieldErrors(form: HTMLFormElement, fields: Record<string, string[]>): void {
	for (const [name, messages] of Object.entries(fields)) {
		const input = form.querySelector<Field>(`[name="${name}"]`);
		const error = input && document.getElementById(`${input.id}-error`);
		if (!input || !error) continue;
		error.textContent = messages.join(" ");
		input.setAttribute("aria-invalid", "true");
	}
	form.querySelector<Field>('[aria-invalid="true"]')?.focus();
}

function initForm(form: HTMLFormElement): void {
	const fields = fieldsIn(form);
	const status = form.querySelector<HTMLElement>(".auth-status");
	const submitButton = form.querySelector<HTMLButtonElement>('[type="submit"]');
	const submit = SUBMITS[form.id];
	watchFields(fields);

	form.addEventListener("submit", async (event) => {
		event.preventDefault();
		if (!validateAll(fields)) return;
		if (!submit) {
			if (status) status.textContent = NOT_AVAILABLE;
			return;
		}

		if (status) status.textContent = "";
		if (submitButton) submitButton.disabled = true;
		try {
			await submit(new FormData(form));
			if (status) status.textContent = "¡Listo! Redirigiendo…";
			location.assign(AFTER_LOGIN_URL);
		} catch (error) {
			if (error instanceof ApiError) {
				showFieldErrors(form, error.fields);
				if (status && Object.keys(error.fields).length === 0) status.textContent = error.message;
			} else if (status) {
				status.textContent = "Algo salió mal. Inténtalo de nuevo.";
			}
			if (submitButton) submitButton.disabled = false;
		}
	});
}

function initPasswordToggles(): void {
	for (const toggle of document.querySelectorAll<HTMLButtonElement>(".auth-toggle-password")) {
		const input = document.getElementById(toggle.getAttribute("aria-controls")!) as Field;
		toggle.addEventListener("click", () => {
			const visible = input.type === "text";
			input.type = visible ? "password" : "text";
			toggle.textContent = visible ? "Mostrar" : "Ocultar";
			toggle.setAttribute("aria-pressed", String(!visible));
			toggle.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
		});
	}
}

function initTermsDialog(): void {
	const dialog = document.querySelector<HTMLDialogElement>("#terms-dialog");
	const checkbox = document.querySelector<Field>("#register-terms");
	if (!dialog) return;

	for (const opener of document.querySelectorAll("[data-open-terms]")) {
		opener.addEventListener("click", () => dialog.showModal());
	}
	dialog.querySelector("[data-terms-accept]")?.addEventListener("click", () => {
		if (checkbox) {
			checkbox.checked = true;
			validate(checkbox);
		}
		dialog.close();
	});
	for (const closer of dialog.querySelectorAll("[data-terms-close]")) {
		closer.addEventListener("click", () => dialog.close());
	}
	// Clic fuera del contenido (sobre el fondo) cierra el cuadro.
	dialog.addEventListener("click", (event) => {
		if (event.target === dialog) dialog.close();
	});
}

export function initAuthForms(): void {
	for (const id of ["login-form", "register-form", "recover-form"]) {
		const form = document.getElementById(id);
		if (form instanceof HTMLFormElement) initForm(form);
	}
	initPasswordToggles();
	initTermsDialog();
}
