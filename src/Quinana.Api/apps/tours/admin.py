from django.contrib import admin

from .models import Destination, Tour


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("title", "destination", "duration_days", "price_usd")
    list_filter = ("destination",)
    search_fields = ("title",)
