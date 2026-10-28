from django import forms

from .models import Tour


class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ["title", "destination", "duration", "description", "price_usd"]
        labels = {
            "title": "Título",
            "destination": "Destino",
            "duration": "Duración",
            "description": "Descripción",
            "price_usd": "Precio (USD)",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej. Galápagos Luxury Cruise"}),
            "destination": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej. Galápagos, Andes, Amazonía"}),
            "duration": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej. 2 días / 1 noche"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
            "price_usd": forms.NumberInput(attrs={"class": "form-input", "step": "0.01", "min": "0"}),
        }
