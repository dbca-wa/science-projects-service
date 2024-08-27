import csv
import os
from django.conf import settings
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import model_to_dict
from django.http import HttpResponse
import requests
from agencies.serializers import (
    TinyBranchSerializer,
    TinyBusinessAreaSerializer,
    TinyAgencySerializer,
)

from projects.models import ProjectMember
from users.serializers import TinyUserSerializer
from users.views import Users
from .models import KeywordTag, PublicStaffProfile, User, UserWork, UserProfile


@admin.action(description="Send About and Expertise to SP")
def copy_about_expertise_to_staff_profile(model_admin, req, selected):
    if len(selected) > 1:
        print("Please select only one")
        return

    users_to_update = User.objects.filter(is_staff=True)
    for user in users_to_update:
        current_about = user.profile.about
        current_expertise = user.profile.expertise

        profile = PublicStaffProfile.objects.get(user=user)
        profile.about = f"<p>{current_about}</p>"
        profile.expertise = f"<p>{current_expertise}</p>"
        profile.save()

    model_admin.message_user(
        req,
        f"Copied profile data over to staff profile for {users_to_update.count()} user(s).",
    )


@admin.action(description="Creates a staff profile for users w/o")
def create_staff_profiles(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    # Filter for users that do not have public profiles
    users_to_update = User.objects.filter(staff_profile__isnull=True)

    # Iterate and create a public staff profile for each user
    for user in users_to_update:
        PublicStaffProfile.objects.create(
            user=user,
            # dbca_position_title="",  # or any default value or logic you want
            # keyword_tags="",
            # about_me="",
            # expertise=""
        )

    model_admin.message_user(
        req, f"public profiles created for {users_to_update.count()} user(s)."
    )


@admin.action(description="Sets the it_asset id ")
def set_it_assets_id(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    # Filter for users that do not have display names set but have first and last names
    users_to_update = User.objects.filter(staff_profile__it_asset_id__isnull=True)

    # Call the API to retrieve the list of users
    api_url = "https://itassets.dbca.wa.gov.au/api/v3/departmentuser/"
    response = requests.get(
        api_url,
        auth=(
            "jarid.prince@dbca.wa.gov.au",
            settings.IT_ASSETS_ACCESS_TOKEN,
        ),
    )

    if response.status_code != 200:
        print("Failed to retrieve data from API")
        return

    api_data = response.json()

    # Iterate through users to update and match them with the API data
    for user in users_to_update:
        matching_record = next(
            (item for item in api_data if item["email"] == user.email), None
        )

        if matching_record:
            staff_profile = PublicStaffProfile.objects.get(user=user)
            staff_profile.it_asset_id = matching_record["id"]
            staff_profile.save()

    model_admin.message_user(
        req, f"public profiles updated for {users_to_update.count()} user(s)."
    )


@admin.action(description="Sets the display names to first and last")
def update_display_names(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    # Filter for users that do not have display names set but have first and last names
    users_to_update = User.objects.filter(
        display_first_name="", display_last_name=""
    ).exclude(first_name="", last_name="")

    # Iterate and update each user's display names
    for user in users_to_update:
        if not user.display_first_name:
            user.display_first_name = user.first_name

        if not user.display_last_name:
            user.display_last_name = user.last_name

        user.save()

    model_admin.message_user(
        req, f"Display names updated for {users_to_update.count()} user(s)."
    )


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

    file_content = []
    dbca_users = []
    other_users = []
    file_content.append(
        "-----------------------------------------------------------\nUnique DBCA Project Leads (Active Projects)\n-----------------------------------------------------------\n"
    )

    for leader in unique_active_project_leads:
        print(
            f"handling leader {leader.email} | {leader.first_name} {leader.last_name}"
        )
        if leader.email.endswith("dbca.wa.gov.au"):
            dbca_users.append(leader)

        else:
            other_users.append(leader)

    for user in dbca_users:
        file_content.append(f"{user.email}\n")

    file_content.append(
        "\n\n-----------------------------------------------------------\nUnique Non-DBCA Emails of Project Leads (Active Projects)\n-----------------------------------------------------------\n"
    )

    for other in other_users:
        projmembers = active_project_leaders.filter(user=other).all()
        file_content.append(
            f"User: {other.email} | {other.first_name} {other.last_name}\nProjects:\n"
        )
        for p in projmembers:
            file_content.append(
                f"\t-Link: https://scienceprojects.dbca.wa.gov.au/projects/{p.project.pk}\n"
            )
            file_content.append(f"\t-Project: {p.project.title}\n\n")

        file_content.append("\n")

    response = HttpResponse(
        content_type="text/plain",
        content="".join(file_content),
    )
    response["Content-Disposition"] = 'attachment; filename="active_project_leads.txt"'

    return response


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = [
        export_selected_users_to_csv,
        export_current_active_project_leads,
        update_display_names,
    ]
    fieldsets = (
        (
            "Profile",
            {
                "fields": (
                    "username",
                    "password",
                    "email",
                    "display_first_name",
                    "display_last_name",
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


@admin.register(PublicStaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    user = TinyUserSerializer(read_only=True)
    list_display = ["user", "is_hidden", "about", "expertise"]
    ordering = ["user"]
    search_fields = [
        "user__display_first_name",  # Search by first name
        "user__display_last_name",  # Search by last name
        "user__first_name",  # Search by first name
        "user__last_name",  # Search by last name
        "user__username",  # Search by username
    ]
    actions = [
        create_staff_profiles,
        export_current_active_project_leads,
        update_display_names,
        copy_about_expertise_to_staff_profile,
        set_it_assets_id,
    ]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    user = TinyUserSerializer(read_only=True)
    list_display = [
        "user",
        "title",
        "middle_initials",
        # "expertise",
        # "about",
        "image",
    ]
    ordering = ["user"]
    search_fields = [
        "user__display_first_name",  # Search by first name
        "user__display_last_name",  # Search by last name
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
        "user__display_first_name",
        "user__last_name",
        "user__display_last_name",
        "branch__name",
    ]


@admin.action(description="Delete unused tags")
def delete_unused_tags(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return
    # Filter out tags that are not associated with any PublicStaffProfile
    unused_tags = KeywordTag.objects.filter(staff_profiles__isnull=True)

    # Count the number of tags before deletion
    num_deleted, _ = unused_tags.delete()

    # Provide feedback to the admin user
    model_admin.message_user(req, f"{num_deleted} unused tags were deleted.")


@admin.register(KeywordTag)
class KeywordTagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")
    actions = [delete_unused_tags]
