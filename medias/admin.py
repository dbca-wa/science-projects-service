# region IMPORTS ==================================================

from django import forms
from django.contrib import admin

from .models import (
    AECEndorsementPDF,
    AgencyImage,
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    LegacyAnnualReportPDF,
    ProjectDocumentPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
    UserAvatar,
)

# endregion ==================================================


# region ADMIN CLASSES ==================================================


class AgencyImageAdminForm(forms.ModelForm):
    class Meta:
        model = AgencyImage
        fields = "__all__"

    file = forms.ImageField(required=True, label="Upload File")


@admin.register(AgencyImage)
class AgencyImageAdmin(admin.ModelAdmin):
    form = AgencyImageAdminForm
    list_display = (
        "agency",
        "file",
        "size_in_mb",
    )

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = AgencyImage.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(ProjectDocumentPDF)
class ProjectDocumentPDFAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "file",
        "size_in_mb",
        "document",
        "project",
    ]

    search_fields = [
        "project",
    ]

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate pdf sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = ProjectDocumentPDF.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} pdf sizes.")


@admin.register(AECEndorsementPDF)
class AECEndorsementPDFAdmin(admin.ModelAdmin):
    list_display = [
        "endorsement",
        "file",
        "size_in_mb",
        "creator",
    ]

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = AECEndorsementPDF.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(AnnualReportPDF)
class AnnualReportPDFAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "report",
        "file",
        "size_in_mb",
        "creator",
    ]

    list_filter = [
        "report",
    ]

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = AnnualReportPDF.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(LegacyAnnualReportPDF)
class LegacyAnnualReportPDFAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "year",
        "file",
        "size_in_mb",
        "creator",
    ]

    list_filter = [
        "year",
    ]

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate file sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_items = (
            LegacyAnnualReportPDF.objects.all()
        )  # Get all ProjectPhoto instances
        for item in all_items:
            if item.file:
                item.size = item.file.size
                item.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} items.")


@admin.register(AnnualReportMedia)
class AnnualReportMediaAdmin(admin.ModelAdmin):
    list_display = [
        "report",
        "kind",
        "file",
        "size_in_mb",
        "uploader",
    ]

    list_filter = [
        "report",
        "kind",
    ]

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = AnnualReportMedia.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(BusinessAreaPhoto)
class BusinessAreaPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "business_area",
        "file",
        "size_in_mb",
        "uploader",
    )

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = BusinessAreaPhoto.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(ProjectPhoto)
class ProjectPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "file",
        "size_in_mb",
        "project",
        "uploader",
    )

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = ProjectPhoto.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(ProjectPlanMethodologyPhoto)
class ProjectPlanMethodologyPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "file",
        "size_in_mb",
        "project_plan",
        "uploader",
    )

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = (
            ProjectPlanMethodologyPhoto.objects.all()
        )  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


@admin.register(UserAvatar)
class UserAvatarAdmin(admin.ModelAdmin):
    list_display = (
        # "old_file",
        "pk",
        "file",
        "size_in_mb",
        "user",
    )

    @admin.display(
        description="Size (MB)",
        ordering="size",
    )
    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    actions = ["recalculate_photo_sizes"]

    @admin.action(description="Recalculate photo sizes")
    def recalculate_photo_sizes(self, request, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return
        updated_count = 0
        all_photos = UserAvatar.objects.all()  # Get all ProjectPhoto instances
        for photo in all_photos:
            if photo.file:
                photo.size = photo.file.size
                photo.save()
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} photos.")


# endregion ==================================================
