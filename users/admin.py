import csv
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import model_to_dict
from django.http import HttpResponse
from agencies.serializers import (
    TinyBranchSerializer,
    TinyBusinessAreaSerializer,
    TinyAgencySerializer,
)

from users.serializers import TinyUserSerializer
from .models import User, UserWork, UserProfile


# CREATE AN EXPORT TO CSV FILE FOR CURRENT ENTRIES IN DB
@admin.action(description="Selected Users to CSV")
def export_selected_users_to_csv(model_admin, req, selected):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'

    field_names = selected[
        0
    ]._meta.fields  # Get the field names from the model's metadata
    writer = csv.DictWriter(response, fieldnames=[field.name for field in field_names])
    writer.writeheader()

    for user in selected:
        user_data = model_to_dict(user, fields=[field.name for field in field_names])
        writer.writerow(user_data)

    return response


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = [
        export_selected_users_to_csv,
    ]
    fieldsets = (
        (
            "Profile",
            {
                "fields": (
                    "username",
                    "password",
                    "email",
                    "first_name",
                    "last_name",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Important Dates",
            {
                "fields": ("last_login", "date_joined"),
                "classes": ("collapse",),
            },
        ),
    )

    list_display = [
        "pk",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_biometrician",
        "is_staff",
        "is_superuser",
    ]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    user = TinyUserSerializer(read_only=True)
    list_display = [
        "user",
        "title",
        "middle_initials",
        "expertise",
        "about",
        "image",
    ]
    ordering = ["user"]
    search_fields = [
        "user__first_name",  # Search by first name
        "user__last_name",  # Search by last name
        "user__username",  # Search by username
    ]


@admin.register(UserWork)
class UserWorkAdmin(admin.ModelAdmin):
    agency = TinyAgencySerializer()
    branch = TinyBranchSerializer()
    business_area = TinyBusinessAreaSerializer()

    list_display = [
        "user",
        "agency",
        "branch",
        "business_area",
    ]

    list_filter = [
        "agency",
        "branch",
        "business_area",
    ]

    search_fields = [
        "business_area__name",
        "user__username",
        "user__first_name",
        "branch__name",
    ]
