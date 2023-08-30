from django.contrib import admin
from .models import Area


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "area_type",
        "created_at",
        "updated_at",
    ]

    list_filter = ["area_type"]

    search_fields = [
        "name",
    ]

    ordering = ["name"]
