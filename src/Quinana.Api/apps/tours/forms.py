from django import forms

from .models import Destination, Tour


class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ["title", "destination", "duration_days", "description", "price_usd"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej. Galápagos Luxury Cruise"}),
            "destination": forms.Select(attrs={"class": "form-input"}),
            "duration_days": forms.NumberInput(attrs={"class": "form-input", "min": "1", "max": str(Tour.MAX_DURATION_DAYS), "step": "1"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
            "price_usd": forms.NumberInput(attrs={"class": "form-input", "step": "0.01", "min": "0.01"}),
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
