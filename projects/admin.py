# region IMPORTS ==============================================

from django.contrib import admin

from locations.models import Area

from .models import (
    ExternalProjectDetails,
    Project,
    ProjectArea,
    ProjectDetail,
    ProjectMember,
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


@admin.action(description="Clean orphaned project memberships")
def clean_orphaned_project_memberships(model_admin, req, selected):
    """
    Remove ProjectMember records where the associated user no longer exists.
    This handles cases where user deletion didn't properly cascade.
    """
    if len(selected) > 1:
        model_admin.message_user(req, "PLEASE SELECT ONLY ONE", level="error")
        return

    from users.models import User

    # Find all ProjectMember records
    all_members = ProjectMember.objects.all()
    orphaned_count = 0
    orphaned_details = []

    for member in all_members:
        # Check if the user exists
        try:
            if (
                member.user is None
                or not User.objects.filter(pk=member.user_id).exists()
            ):
                orphaned_details.append(
                    f"Project: {member.project.title} (ID: {member.project.pk}), "
                    f"User ID: {member.user_id}, Role: {member.role}"
                )
                member.delete()
                orphaned_count += 1
        except Exception as e:
            orphaned_details.append(f"Error checking member {member.pk}: {str(e)}")
            member.delete()
            orphaned_count += 1

    if orphaned_count > 0:
        message = (
            f"Cleaned {orphaned_count} orphaned project membership(s):\n"
            + "\n".join(orphaned_details[:10])
        )
        if len(orphaned_details) > 10:
            message += f"\n... and {len(orphaned_details) - 10} more"
        model_admin.message_user(req, message, level="warning")
    else:
        model_admin.message_user(
            req, "No orphaned project memberships found.", level="success"
        )


@admin.action(description="Report orphaned data")
def report_orphaned_data(model_admin, req, selected):
    """
    Generate a report of all orphaned data without deleting anything.
    Checks ProjectMember, ProjectDetail, and other models for null/missing user references.
    """
    if len(selected) > 1:
        model_admin.message_user(req, "PLEASE SELECT ONLY ONE", level="error")
        return

    from users.models import User

    report = []

    # Check ProjectMember for orphaned users
    orphaned_members = []
    for member in ProjectMember.objects.all():
        try:
            if (
                member.user is None
                or not User.objects.filter(pk=member.user_id).exists()
            ):
                orphaned_members.append(
                    f"  - ProjectMember ID {member.pk}: Project '{member.project.title}' (ID: {member.project.pk}), "
                    f"User ID: {member.user_id}, Role: {member.role}"
                )
        except Exception:
            orphaned_members.append(
                f"  - ProjectMember ID {member.pk}: Error accessing user data"
            )

    if orphaned_members:
        report.append(f"Orphaned ProjectMembers ({len(orphaned_members)}):")
        report.extend(orphaned_members[:20])
        if len(orphaned_members) > 20:
            report.append(f"  ... and {len(orphaned_members) - 20} more")

    # Check ProjectDetail for null user references
    orphaned_details = []
    for detail in (
        ProjectDetail.objects.filter(creator__isnull=True)
        | ProjectDetail.objects.filter(modifier__isnull=True)
        | ProjectDetail.objects.filter(owner__isnull=True)
    ):
        issues = []
        if detail.creator is None:
            issues.append("creator=null")
        if detail.modifier is None:
            issues.append("modifier=null")
        if detail.owner is None:
            issues.append("owner=null")
        orphaned_details.append(
            f"  - ProjectDetail ID {detail.pk}: Project '{detail.project.title}' ({', '.join(issues)})"
        )

    if orphaned_details:
        report.append(f"\nProjectDetails with null users ({len(orphaned_details)}):")
        report.extend(orphaned_details[:20])
        if len(orphaned_details) > 20:
            report.append(f"  ... and {len(orphaned_details) - 20} more")

    if report:
        full_report = "ORPHANED DATA REPORT:\n" + "\n".join(report)
        model_admin.message_user(req, full_report, level="warning")
    else:
        model_admin.message_user(req, "No orphaned data found!", level="success")


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

    @admin.display(description="Areas")
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
        convert_ext_peer_to_consulted,
        convert_ext_collaborator_to_consulted,
        clean_orphaned_project_memberships,
        report_orphaned_data,
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
