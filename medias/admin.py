from django.contrib import admin
from .models import (
    AnnualReportMedia,
    BusinessAreaPhoto,
    UserAvatar,
    ProjectPhoto,
    AgencyImage,
    ProjectDocumentPDF,
)

from django import forms


class AgencyImageAdminForm(forms.ModelForm):
    class Meta:
        model = AgencyImage
        fields = "__all__"

    file = forms.ImageField(required=True, label="Upload File")
    # old_file = forms.ImageField(required=False, label="Upload Old File")


@admin.register(AgencyImage)
class AgencyImageAdmin(admin.ModelAdmin):
    form = AgencyImageAdminForm
    list_display = (
        "agency",
        "file",
    )


@admin.register(ProjectDocumentPDF)
class ProjectDocumentPDFAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        # "old_file",
        "file",
        "document",
        "project",
    ]

    search_fields = [
        "project",
    ]

    # list_filter = [
    #     "project",
    #     "document",
    # ]


@admin.register(AnnualReportMedia)
class AnnualReportMediaAdmin(admin.ModelAdmin):
    list_display = [
        "report",
        "kind",
        # "old_file",
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
        # "old_file",
        "file",
        "uploader",
    )


@admin.register(ProjectPhoto)
class ProjectPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        # "old_file",
        "file",
        "uploader",
    )


@admin.register(UserAvatar)
class UserAvatarAdmin(admin.ModelAdmin):
    list_display = (
        # "old_file",
        "file",
        "user",
    )
