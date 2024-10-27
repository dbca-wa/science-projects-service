# region IMPORTS ==============================================

from django.contrib import admin
from locations.models import Area
from .models import (
    ExternalProjectDetails,
    Project,
    ProjectArea,
    ProjectMember,
    ProjectDetail,
    StudentProjectDetails,
)

# endregion ==============================================

# region ADMIN ACTION ==============================================


# A function to convert "External Peer" roles to "Consulted Peers" (externalpeer --> consulted)
@admin.action(description="Convert EXT Peer to Consulted")
def convert_ext_peer_to_consulted(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    roles_to_convert = [
        ProjectMember.RoleChoices.EXTERNALPEER,
    ]
    new_role = ProjectMember.RoleChoices.CONSULTED

    # Update the role for all matching users
    ProjectMember.objects.filter(role__in=roles_to_convert).update(role=new_role)
    return


# A function to convert "External Collaborator" roles to "Consulted Peers" (externalcol --> consulted)
@admin.action(description="Convert EXT Collaborator to Consulted")
def convert_ext_collaborator_to_consulted(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return

    roles_to_convert = [
        ProjectMember.RoleChoices.EXTERNALCOL,
    ]
    new_role = ProjectMember.RoleChoices.CONSULTED

    # Update the role for all matching users
    ProjectMember.objects.filter(role__in=roles_to_convert).update(role=new_role)
    return


# endregion ==============================================

# region ADMIN CLASSES ==============================================


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    # kind = ProjectCategorySerializer()
    list_display = [
        "title",
        "year",
        "kind",
        "status",
        "deletion_requested",
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

        actions = [
            # set_is_leader_to_true,
            convert_ext_peer_to_consulted,
            convert_ext_collaborator_to_consulted,
        ]

    @admin.register(ProjectDetail)
    class ProjectDetailAdmin(admin.ModelAdmin):
        list_display = [
            "project",
            "creator",
            "modifier",
            "owner",
        ]

        search_fields = [
            "project__title",
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

    @admin.action(description="Dupe description on empty")
    def update_external_description_with_project_description_if_empty(
        model_admin, req, selected
    ):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return

        updated_count = 0

        sections_to_populate = [
            None,
            "",
            "<p></p>",
            '<p class="editor-p-light" dir="ltr"><span style="white-space: pre-wrap;"></span></p>',
        ]
        # Update the role for all matching users
        exts = ExternalProjectDetails.objects.all()
        for obj in exts:
            if obj.description in sections_to_populate:
                # Fetch the related project
                project_description = obj.project.description

                # Update the description field if needed
                if project_description:
                    obj.description = project_description
                    obj.save()
                    updated_count += 1
        model_admin.message_user(req, f"Successfully updated {updated_count} projects.")
        return

    @admin.action(
        description="Create ExternalProjectDetails for external projects without details"
    )
    def create_external_details_if_missing(model_admin, req, selected):
        if len(selected) > 1:
            print("PLEASE SELECT ONLY ONE")
            return

        updated_count = 0
        queryset = Project.objects.filter(
            kind=Project.CategoryKindChoices.EXTERNAL
        ).all()
        # Iterate over the selected projects
        for project in queryset:
            # Check if an ExternalProjectDetails instance already exists for this project
            if not hasattr(project, "external_project_info"):
                # Create a new ExternalProjectDetails instance
                ExternalProjectDetails.objects.create(
                    project=project,
                    old_id=project.old_id,  # Assuming you want to use the project's old_id or handle it accordingly
                )
                updated_count += 1
        model_admin.message_user(req, f"Successfully updated {updated_count} projects.")

    @admin.register(ExternalProjectDetails)
    class ExternalProjectDetailAdmin(admin.ModelAdmin):
        list_display = [
            "pk",
            "project",
            "collaboration_with",
            "budget",
            "description",
        ]

        search_fields = [
            "project__title",
            "pk",
        ]

        list_filter = [
            "collaboration_with",
        ]

        ordering = ["project__title"]


# endregion ==============================================
