from django.contrib import admin
from adminoptions.models import AdminOptions, AdminTask


@admin.register(AdminOptions)
class AdminOptionsAdmin(admin.ModelAdmin):
    list_display = [
        "email_options",
        "updated_at",
    ]


@admin.register(AdminTask)
class AdminTaskAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "project",
        "action",
        "requestor",
        "reasoning",
        "status",
    ]
