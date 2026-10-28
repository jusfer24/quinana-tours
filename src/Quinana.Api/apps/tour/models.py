from django.db import models

# Create your models here.
class Tour(models.Model):
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=100) # ej: Galapagos, Andes
    duration = models.TextField(max_length=100) # ej: 2 Dias / 1 Noche
    description = models.TextField()
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title