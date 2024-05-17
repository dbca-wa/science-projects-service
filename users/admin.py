import csv
import os
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

from projects.models import ProjectMember
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


# A function to output the project leaders of active projects for latest report
@admin.action(description="Export Active Project Leaders")
def export_current_active_project_leads(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return
    active_project_leaders = ProjectMember.objects.filter(
        is_leader=True, project__status="active"
    ).all()
    unique_active_project_leads = list(
        set(
            lead_member_object.user
            for lead_member_object in active_project_leaders
            if lead_member_object.user.is_active
        )
    )
    file_location = os.path.dirname(os.path.realpath(__file__)) + "/pls.txt"

    with open(file_location, "w+") as file:
        dbca_users = []
        other_users = []
        for leader in unique_active_project_leads:
            print(
                f"handling leader {leader.email} | {leader.first_name} {leader.last_name}"
            )
            if leader.email.endswith("dbca.wa.gov.au"):
                dbca_users.append(leader)

            else:
                other_users.append(leader)

        file.write(
            "-----------------------------------------------------------\nUnique DBCA Project Leads (Active Projects)\n-----------------------------------------------------------\n"
        )
        for user in dbca_users:
            file.write(f"{user.email}\n")

        file.write(
            "\n\n-----------------------------------------------------------\nUnique Non-DBCA Emails of Project Leads (Active Projects)\n-----------------------------------------------------------\n"
        )
        for other in other_users:
            projmembers = active_project_leaders.filter(user=other).all()
            file.write(f"User: {other.email} | {other.first_name} {other.last_name}\n")
            for p in projmembers:
                file.write(f"\t-Project: {p.project.title}\n")
                file.write(
                    f"\t\tLink: https://scienceprojects.dbca.wa.gov.au/projects/{p.project.pk}\n"
                )
            file.write("\n")


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = [
        export_selected_users_to_csv,
        export_current_active_project_leads,
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
        "is_aec",
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
