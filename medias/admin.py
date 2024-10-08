# region IMPORTS ==================================================

from django.contrib import admin
from django import forms
from .models import (
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    LegacyAnnualReportPDF,
    UserAvatar,
    ProjectPhoto,
    AgencyImage,
    ProjectDocumentPDF,
    AECEndorsementPDF,
    ProjectPlanMethodologyPhoto,
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

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


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

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate pdf sizes"


@admin.register(AECEndorsementPDF)
class AECEndorsementPDFAdmin(admin.ModelAdmin):
    list_display = [
        "endorsement",
        "file",
        "size_in_mb",
        "creator",
    ]

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


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

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


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

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate file sizes"


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

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


@admin.register(BusinessAreaPhoto)
class BusinessAreaPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "business_area",
        "file",
        "size_in_mb",
        "uploader",
    )

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


@admin.register(ProjectPhoto)
class ProjectPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "file",
        "size_in_mb",
        "project",
        "uploader",
    )

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


@admin.register(ProjectPlanMethodologyPhoto)
class ProjectPlanMethodologyPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "file",
        "size_in_mb",
        "project_plan",
        "uploader",
    )

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


@admin.register(UserAvatar)
class UserAvatarAdmin(admin.ModelAdmin):
    list_display = (
        # "old_file",
        "pk",
        "file",
        "size_in_mb",
        "user",
    )

    def size_in_mb(self, obj):
        if obj.size:
            return "{:.2f} MB".format(obj.size / (1024 * 1024))
        else:
            return "Unknown"

    size_in_mb.admin_order_field = "size"  # Enables sorting by size
    size_in_mb.short_description = "Size (MB)"

    actions = ["recalculate_photo_sizes"]

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

    recalculate_photo_sizes.short_description = "Recalculate photo sizes"


# endregion ==================================================
