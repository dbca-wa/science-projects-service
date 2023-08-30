from django.contrib import admin
from .models import (
    AnnualReportMedia,
    BusinessAreaPhoto,
    UserAvatar,
    ProjectPhoto,
    AgencyImage,
)


@admin.register(AnnualReportMedia)
class AnnualReportMediaAdmin(admin.ModelAdmin):
    list_display = [
        "report",
        "kind",
        "old_file",
        "file",
        "uploader",
    ]

    list_filter = [
        "report",
        "kind",
    ]


@admin.register(BusinessAreaPhoto)
class BusinessAreaPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "business_area",
        "old_file",
        "file",
        "uploader",
    )


@admin.register(ProjectPhoto)
class ProjectPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "old_file",
        "file",
        "uploader",
    )


@admin.register(AgencyImage)
class AgencyImageAdmin(admin.ModelAdmin):
    list_display = (
        "agency",
        "file",
    )


@admin.register(UserAvatar)
class UserAvatarAdmin(admin.ModelAdmin):
    list_display = (
        "old_file",
        "file",
        "user",
    )
