from django.contrib import admin
from adminoptions.models import AdminOptions


@admin.register(AdminOptions)
class AdminOptionsAdmin(admin.ModelAdmin):
    list_display = [
        "email_options",
        "updated_at",
    ]
