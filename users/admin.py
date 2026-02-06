# region IMPORTS ======================================
import csv, requests
from datetime import datetime
from operator import is_
import os
import pandas as pd
from django.conf import settings
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import model_to_dict
from django.http import HttpResponse

# Project Imports --------------------
from .models import KeywordTag, PublicStaffProfile, User, UserWork, UserProfile
from agencies.serializers import (
    TinyBranchSerializer,
    TinyBusinessAreaSerializer,
    TinyAgencySerializer,
)
from projects.models import ProjectMember
from users.serializers import TinyUserSerializer
from users.views import StaffProfiles, Users

# endregion ===========================================


# region adminactions =================================


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


@admin.action(description="Hide all staff profiles")
def hide_all_staff_profiles(model_admin, req, selected):
    if len(selected) > 1:
        print("Please select only one")
        return
    # Find all users that are staff and have a public profile
    users_to_update = User.objects.filter(
        is_staff=True,
        staff_profile__isnull=False,
    )

    # Update the staff profiles through the related StaffProfile model
    PublicStaffProfile.objects.filter(user__in=users_to_update).update(is_hidden=True)

    model_admin.message_user(
        req,
        f"Staff profiles were hidden for {users_to_update.count()} user(s).",
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
        )

    model_admin.message_user(
        req, f"public profiles created for {users_to_update.count()} user(s)."
    )


@admin.action(description="Generate CSV of active staff data")
def generate_active_staff_csv(model_admin, request, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    # Create the HttpResponse object with CSV header
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="staff_data_{timestamp}.csv"'
        },
    )

    # Create CSV writer
    writer = csv.writer(response)

    # Write header row
    writer.writerow(
        [
            "ID",
            "Name",
            "Title",
            "Location",
            "Email",
            "Division",
            "Unit",
            "Employee ID",
            "Manager",
            "Manager Email",
            "Manager ID",
        ]
    )

    # Get all active staff users
    users = User.objects.filter(is_staff=True, is_active=True).exclude(
        staff_profile__is_hidden=True
    )

    # Fetch IT Assets data
    try:
        response_it = requests.get(
            settings.IT_ASSETS_URL,
            auth=(settings.IT_ASSETS_USER, settings.IT_ASSETS_ACCESS_TOKEN),
        )

        if response_it.status_code == 200:
            it_asset_data = response_it.json()
            # Create lookup dictionary
            it_asset_data_by_email = {
                user_data["email"]: user_data
                for user_data in it_asset_data
                if "email" in user_data
            }

            # Write data rows
            for user in users:
                user_data = it_asset_data_by_email.get(user.email, {})

                # Only include BCS division staff
                if (
                    user_data.get("unit")
                    == "Biodiversity and Conservation Science Division"
                    # user_data.get("division")
                    # == "Biodiversity and Conservation Science"
                    # or user_data.get("division")
                    # == "Dept Biodiversity, Conservation and Attractions"
                ):
                    writer.writerow(
                        [
                            user_data.get("id", ""),
                            f"{user.first_name} {user.last_name}",
                            user_data.get("title", ""),
                            user_data.get("location", {}).get("name", ""),
                            user.email,
                            user_data.get("division", ""),
                            user_data.get("unit", ""),
                            user_data.get("employee_id", ""),
                            user_data.get("manager", {}).get("name", ""),
                            user_data.get("manager", {}).get("email", ""),
                            user_data.get("manager", {}).get("id", ""),
                        ]
                    )
        else:
            model_admin.message_user(
                request,
                f"Failed to fetch IT Assets data: {response_it.status_code}",
                level="ERROR",
            )
            return None

    except Exception as e:
        model_admin.message_user(
            request, f"Error generating CSV: {str(e)}", level="ERROR"
        )
        return None

    model_admin.message_user(
        request, "Staff CSV generated successfully!", level="SUCCESS"
    )

    return response


@admin.action(description="Sets the it_asset id ")
def set_it_assets_id(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    # Filter for users that do not have display names set but have first and last names
    users_to_update = User.objects.filter(staff_profile__it_asset_id__isnull=True)

    # Call the API to retrieve the list of users
    api_url = settings.IT_ASSETS_URL
    response = requests.get(
        api_url,
        auth=(
            settings.IT_ASSETS_USER,
            settings.IT_ASSETS_ACCESS_TOKEN,
        ),
    )

    if response.status_code != 200:
        if settings.IT_ASSETS_USER == None:
            settings.LOGGER.warning("No IT_ASSETS_USER found in settings/env")
        if settings.IT_ASSETS_ACCESS_TOKEN == None:
            settings.LOGGER.warning("No IT_ASSETS_ACCESS_TOKEN found in settings/env")
        settings.LOGGER.error(
            f"Failed to retrieve data from API:\n{response.status_code}: {response.text}"
        )
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


# endregion ===========================================

# region ADMIN REGISTRATION ===========================


@admin.register(KeywordTag)
class KeywordTagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")
    actions = [delete_unused_tags]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = [
        hide_all_staff_profiles,
        generate_active_staff_csv,
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


# endregion ===========================================
