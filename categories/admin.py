from django.contrib import admin
from .models import ProjectCategory


# Register your models here.
@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "kind",
    ]

    list_filter = [
        "kind",
    ]
