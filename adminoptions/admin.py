from django.contrib import admin
from adminoptions.models import AdminOptions, AdminTask, Caretaker


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
        "status",
        "action",
        "requester",
        "created_at",
        "reason",
        "project",
    ]


@admin.register(Caretaker)
class CaretakerAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "user",
        "caretaker",
        "reason",
        "start_date",
        "end_date",
        "created_at",
    ]
