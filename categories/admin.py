from django.contrib import admin
from .models import ProjectCategory


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "kind",
    ]

    list_filter = [
        "kind",
    ]
