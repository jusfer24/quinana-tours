from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify

from . import iconos
from .models import Categoria, Destination, Tour

FOTO_MAX_MB = 5
FOTO_FORMATOS = ["jpg", "jpeg", "png", "webp"]
FOTO_AYUDA = f"JPG, PNG o WebP de hasta {FOTO_MAX_MB} MB. Mejor horizontal y de al menos 1600 px de ancho."


def validar_peso_foto(foto):
    if foto and foto.size > FOTO_MAX_MB * 1024 * 1024:
        raise forms.ValidationError(f"La foto pesa más de {FOTO_MAX_MB} MB. Redúcela e inténtalo de nuevo.")


class FotoInput(forms.ClearableFileInput):
    """Selector de archivo con la casilla para quitar la foto actual (sin el «Actualmente/Modificar»)."""

    template_name = "tours/widgets/foto.html"

    def __init__(self, quitar_texto, attrs=None):
        super().__init__(attrs)
        self.quitar_texto = quitar_texto

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["quitar_texto"] = self.quitar_texto
        return context


def campo_foto(label, quitar_texto):
    return forms.ImageField(
        label=label,
        required=False,
        help_text=FOTO_AYUDA,
        validators=[FileExtensionValidator(FOTO_FORMATOS), validar_peso_foto],
        widget=FotoInput(quitar_texto, attrs={"class": "form-input", "accept": "image/jpeg,image/png,image/webp"}),
        error_messages={
            "invalid_image": "El archivo no es una imagen válida. Sube una foto JPG, PNG o WebP.",
            "invalid_extension": "Formato no admitido. Sube una foto JPG, PNG o WebP.",
        },
    )


def tendra_foto(form, cleaned):
    """Si el registro quedará con foto al guardar: una nueva, o la actual si no se marcó «Borrar».

    Django deja en cleaned["foto"] el archivo nuevo, la foto actual si no se tocó el campo,
    o False si se marcó «Borrar». Si el campo tiene errores, se mira la foto actual.
    """
    if "foto" in cleaned:
        return bool(cleaned["foto"])
    return bool(form.instance.foto)


def _texto(placeholder="", **attrs):
    return forms.TextInput(attrs={"class": "form-input", "placeholder": placeholder, **attrs})


def _descripcion_foto():
    """La descripción de la foto suele ser una frase larga: caja de varias líneas."""
    return forms.Textarea(attrs={"class": "form-input", "rows": 3, "maxlength": 250})


class IconoSelect(forms.RadioSelect):
    """Opciones de ícono como una cuadrícula de botones con el dibujo de cada uno."""

    template_name = "tours/widgets/iconos.html"

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option["svg"] = iconos.trazo(option["value"])
        return option


class TourForm(forms.ModelForm):
    foto = campo_foto("Subir foto propia", "Quitar la foto propia (vuelve a la del destino)")

    class Meta:
        model = Tour
        fields = ["title", "destination", "categorias", "duration_days", "description", "price_usd", "foto", "foto_alt"]
        labels = {"foto_alt": "Descripción de la foto", "categorias": "Tipo de viaje"}
        help_texts = {
            "categorias": "Marca todas las que apliquen: en el sitio se puede filtrar los tours por tipo de viaje.",
            "description": "Se muestran unas 3 líneas en la tarjeta del sitio.",
            "foto_alt": "Qué se ve en la foto, para lectores de pantalla y Google. Ej.: «Kayak entre manglares».",
        }
        widgets = {
            "title": _texto("Ej. Galápagos Luxury Cruise"),
            "destination": forms.Select(attrs={"class": "form-input"}),
            "categorias": forms.CheckboxSelectMultiple(),
            "duration_days": forms.NumberInput(attrs={"class": "form-input", "min": "1", "max": str(Tour.MAX_DURATION_DAYS), "step": "1"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
            "price_usd": forms.NumberInput(attrs={"class": "form-input", "step": "0.01", "min": "0.01"}),
            "foto_alt": _descripcion_foto(),
        }
        error_messages = {
            "destination": {
                "required": "Selecciona un destino de la lista.",
                "invalid_choice": "El destino seleccionado no existe. Elige uno de la lista.",
            },
            "duration_days": {
                "required": "Indica la duración en días.",
                "invalid": "La duración debe ser un número entero de días.",
            },
            "price_usd": {
                "required": "Indica el precio.",
                "invalid": "Ingresa un precio válido (por ejemplo 1500.00).",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination"].queryset = Destination.objects.all()
        self.fields["destination"].empty_label = "— Selecciona un destino —"

    def clean_title(self):
        title = " ".join(self.cleaned_data["title"].split())
        if len(title) < 3:
            raise forms.ValidationError("El título debe tener al menos 3 caracteres.")
        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 10:
            raise forms.ValidationError("La descripción debe tener al menos 10 caracteres.")
        return description

    def clean(self):
        cleaned = super().clean()
        if tendra_foto(self, cleaned) and not cleaned.get("foto_alt", "").strip():
            self.add_error("foto_alt", "Describe la foto: la leen los lectores de pantalla y Google.")
        return cleaned


class DestinationForm(forms.ModelForm):
    foto = campo_foto("Subir foto", "Quitar la foto actual")

    class Meta:
        model = Destination
        fields = [
            "name", "name_en", "frase", "frase_en",
            "foto", "foto_alt", "foto_alt_en",
            "orden",
        ]
        labels = {"name": "Nombre", "name_en": "Nombre en inglés"}
        help_texts = {
            "frase": "Aparece bajo el nombre en la sección «Destinos».",
            "orden": "Los destinos se muestran de menor a mayor.",
        }
        widgets = {
            "name": _texto("Ej. Galápagos"),
            "name_en": _texto("Ej. Galápagos"),
            "frase": _texto("Ej. Islas encantadas"),
            "frase_en": _texto("Ej. The Enchanted Isles"),
            "foto_alt": _descripcion_foto(),
            "foto_alt_en": _descripcion_foto(),
            "orden": forms.NumberInput(attrs={"class": "form-input", "min": "0", "step": "1"}),
        }
        error_messages = {"name": {"required": "Indica el nombre del destino."}}

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        repetido = Destination.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError("Ya existe un destino con ese nombre.")
        return name

    def clean(self):
        cleaned = super().clean()
        if tendra_foto(self, cleaned):
            for campo in ("foto_alt", "foto_alt_en"):
                if not cleaned.get(campo, "").strip():
                    self.add_error(campo, "Describe la foto: la leen los lectores de pantalla y Google.")
        return cleaned

    def save(self, commit=True):
        # Las fotos que sube el equipo son propias: al cambiar o quitar la foto se borra el
        # crédito de la anterior (las cuatro fotos iniciales son de Wikimedia, con licencia CC).
        destino = super().save(commit=False)
        if "foto" in self.changed_data:
            destino.credito_tema = destino.credito_autor = destino.credito_licencia = destino.credito_url = ""
        if commit:
            destino.save()
        return destino


class CategoriaForm(forms.ModelForm):
    """El slug (clave del filtro en el sitio) se genera del nombre al crear y no cambia al editar."""

    icono = forms.ChoiceField(
        label="Elige el ícono de la categoría",
        choices=iconos.OPCIONES,
        required=False,
        widget=IconoSelect,
        help_text="Se muestra junto al nombre en el filtro y en las etiquetas de los tours del sitio.",
        error_messages={"invalid_choice": "Elige un ícono de la lista."},
    )

    class Meta:
        model = Categoria
        fields = ["nombre", "nombre_en", "icono", "orden"]
        labels = {"nombre": "Nombre", "nombre_en": "Nombre en inglés"}
        help_texts = {"orden": "Los botones del filtro del sitio se muestran de menor a mayor."}
        widgets = {
            "nombre": _texto("Ej. Aventura"),
            "nombre_en": _texto("Ej. Adventure"),
            "orden": forms.NumberInput(attrs={"class": "form-input", "min": "0", "step": "1"}),
        }
        error_messages = {"nombre": {"required": "Indica el nombre de la categoría."}}

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        repetida = Categoria.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetida.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre.")
        if not slugify(nombre):
            raise forms.ValidationError("El nombre debe tener letras o números.")
        return nombre

    def save(self, commit=True):
        categoria = super().save(commit=False)
        if not categoria.slug:
            base = slugify(categoria.nombre)[:110]
            slug, n = base, 2
            while Categoria.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            categoria.slug = slug
        if commit:
            categoria.save()
        return categoria
