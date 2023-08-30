from django.contrib import admin

from locations.models import Area
from .models import (
    ExternalProjectDetails,
    Project,
    ProjectArea,
    ResearchFunction,
    ProjectMember,
    ProjectDetail,
    StudentProjectDetails,
)
from categories.serializers import ProjectCategorySerializer


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    # kind = ProjectCategorySerializer()
    list_display = [
        "title",
        "year",
        "kind",
        "status",
        "business_area",
    ]

    search_fields = [
        "old_id",
        "title",
        "tagline",
        "description",
    ]

    list_filter = [
        "kind",
        "status",
        "year",
        "business_area",
    ]

    ordering = ["title"]


@admin.register(ResearchFunction)
class ResearchFunctionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "leader",
        "is_active",
    ]

    list_filter = [
        "is_active",
    ]

    search_fields = [
        "name",
        "description",
    ]

    ordering = ["name"]


@admin.register(ProjectArea)
class ProjectAreaAdmin(admin.ModelAdmin):
    list_display = [
        "project_id",
        "formatted_areas",
    ]

    def project_id(self, obj):
        return obj.project.id

    def formatted_areas(self, obj):
        areas = obj.areas  # Access the list of area IDs directly
        area_info = []
        for area_id in areas:
            try:
                area = Area.objects.get(pk=area_id)  # Fetch the related Area object
                area_info.append(f"{area.name} ({area.area_type})")
            except Area.DoesNotExist:
                pass
        return ", ".join(area_info)

    formatted_areas.short_description = "Areas"  # Custom column header

    search_fields = [
        "project__title",
    ]

    list_filter = ["project__id"]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "is_leader",
        "project",
    ]

    search_fields = [
        "user__username",
        "project__title",
    ]

    list_filter = [
        "is_leader",
        "role",
    ]

    def set_is_leader_to_true(self, request, queryset):
        project_members_by_project = {}
        projects_without_leader = []

        # Group members by project
        for member in queryset:
            project_id = member.project_id
            if project_id not in project_members_by_project:
                project_members_by_project[project_id] = []
            project_members_by_project[project_id].append(member)

        # Check each project for leaders and set the first member as the leader if none found
        for project_id, members in project_members_by_project.items():
            has_leader = any(member.is_leader for member in members)

            if not has_leader:
                project_detail = ProjectDetail.objects.filter(
                    project_id=project_id
                ).first()
                if project_detail:
                    creator_is_member = any(
                        member.user == project_detail.creator for member in members
                    )
                    project_owner_is_member = any(
                        member.user == project_detail.owner for member in members
                    )

                    # Check if there is a user with the role "supervising" or "academicsuper"
                    supervising_user = next(
                        (
                            member
                            for member in members
                            if member.role in ["supervising", "academicsuper"]
                        ),
                        None,
                    )

                    if supervising_user:
                        # Set the first member with role "supervising" or "academicsuper" as the leader
                        supervising_user.is_leader = True
                        supervising_user.save()
                    elif creator_is_member:
                        # Set the creator as the leader
                        creator_member = next(
                            (
                                member
                                for member in members
                                if member.user == project_detail.creator
                            ),
                            None,
                        )
                        if creator_member:
                            creator_member.is_leader = True
                            creator_member.save()
                    elif project_owner_is_member:
                        # Set the project owner as the leader
                        owner_member = next(
                            (
                                member
                                for member in members
                                if member.user == project_detail.owner
                            ),
                            None,
                        )
                        if owner_member:
                            owner_member.is_leader = True
                            owner_member.save()
                    else:
                        # Exclude members with roles "externalcol", "externalpeer", "group", "consulted", "student"
                        non_leader_roles = [
                            "externalcol",
                            "externalpeer",
                            "group",
                            "consulted",
                            "student",
                        ]
                        eligible_members = [
                            member
                            for member in members
                            if member.role not in non_leader_roles
                        ]
                        if eligible_members:
                            # Set the first user from the remaining eligible members as the leader
                            first_member = eligible_members[0]
                            first_member.is_leader = True
                            first_member.save()
                        else:
                            # Set the first member as the leader if no eligible members found
                            first_member = members[0]
                            first_member.is_leader = True
                            first_member.save()
                else:
                    # Add the project ID to the list if no ProjectDetail is found
                    projects_without_leader.append(project_id)

        # Display messages
        total_members_updated = queryset.count()
        if total_members_updated > 0:
            self.message_user(
                request,
                f"Updated {total_members_updated} members' is_leader field to True.",
            )

        if projects_without_leader:
            self.message_user(
                request,
                f"No leaders found for projects with IDs: {', '.join(map(str, projects_without_leader))}",
            )

    set_is_leader_to_true.short_description = (
        "Set is_leader to True for members who are project owners"
    )

    actions = [set_is_leader_to_true]


@admin.register(ProjectDetail)
class ProjectDetailAdmin(admin.ModelAdmin):
    # kind = ProjectCategorySerializer()
    list_display = [
        "project",
        "creator",
        "modifier",
        "owner",
    ]

    search_fields = [
        "project__title",
    ]

    list_filter = [
        "research_function",
    ]

    ordering = ["project__title"]


@admin.register(StudentProjectDetails)
class StudentProjectDetailAdmin(admin.ModelAdmin):
    # kind = ProjectCategorySerializer()
    list_display = [
        "project",
        "level",
        "organisation",
    ]

    search_fields = [
        "project__title",
    ]

    list_filter = [
        "level",
    ]

    ordering = ["project__title"]


@admin.register(ExternalProjectDetails)
class StudentProjectDetailAdmin(admin.ModelAdmin):
    # kind = ProjectCategorySerializer()
    list_display = [
        "project",
        "collaboration_with",
        "budget",
        "description",
    ]

    search_fields = [
        "project__title",
    ]

    list_filter = [
        "collaboration_with",
    ]

    ordering = ["project__title"]
