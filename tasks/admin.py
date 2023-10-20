from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_type",
        "user",
        "name",
        "status",
        "notes",
        "document",
    )

    list_filter = (
        "task_type",
        "status",
    )

    search_fields = [
        "name",
        "description",
        "user__username",
        "document__project__title",
    ]

    ordering = ["-created_at"]
