# region IMPORTS ========================================================================================================

import ast
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.db.models import Max
from .models import (
    AnnualReport,
    CustomPublication,
    ProjectDocument,
    ConceptPlan,
    ProjectPlan,
    Endorsement,
    ProgressReport,
    StudentReport,
    ProjectClosure,
)

# endregion ========================================================================================================


User = get_user_model()


class UserFilterWidget(FilteredSelectMultiple):
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def format_value(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = ast.literal_eval(value)
        if isinstance(value, int):
            value = [str(value)]  # Convert the value to a string
        return [str(v) for v in value]  # Convert each value to a string


# region Publication Admin ========================================================================================================


@admin.register(CustomPublication)
class CustomPublicationAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "public_profile",
        "title",
        "year",
    )

    ordering = ["-year"]

    list_filter = ("year",)

    search_fields = ["title"]


# endregion ========================================================================================================


# region Admin Actions ========================================================================================================
@admin.action(
    description="(Project/Concept Plans) Provide all approvals if Next Doc exists"
)
def provide_final_approval_for_docs_if_next_exist(model_admin, req, selected):
    if len(selected) != 1:
        print("PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS")
        return
    try:
        # Get docs of each type that do not have corresponding data on the model they refer to
        all_docs = ProjectDocument.objects.all()
        doc_approval_update_count = 0
        doc_process_count = 0
        for doc in all_docs:
            doc_process_count += 1
            next_exists = False
            if doc.kind == ProjectDocument.CategoryKindChoices.CONCEPTPLAN:
                next_exists = ProjectDocument.objects.filter(
                    project=doc.project,
                    kind=ProjectDocument.CategoryKindChoices.PROJECTPLAN,
                ).exists()
            elif doc.kind == ProjectDocument.CategoryKindChoices.PROJECTPLAN:
                next_exists = ProjectDocument.objects.filter(
                    project=doc.project,
                    kind=ProjectDocument.CategoryKindChoices.PROGRESSREPORT,
                ).exists()
            else:
                next_exists = False

            if next_exists and doc.directorate_approval_granted == False:
                doc.project_lead_approval_granted = True
                doc.business_area_lead_approval_granted = True
                doc.directorate_approval_granted = True
                doc_approval_update_count += 1
        print(
            f"Provided full approvals for docs! {doc_approval_update_count}/{doc_process_count} documents didn't have full approval, but the next doc type existed."
        )
    except Exception as e:
        print(e)
    return


@admin.action(description="Delete unlinked docs")
def delete_unlinked_docs(model_admin, req, selected):
    if len(selected) != 1:
        print("PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS")
        return

    try:
        # Get docs of each type that do not have corresponding data on the model they refer to
        all_docs = ProjectDocument.objects.all()
        doc_deletion_count = 0
        doc_process_count = 0
        for doc in all_docs:
            doc_process_count += 1
            if doc.has_project_document_data() == False:
                doc.delete()
                doc_deletion_count += 1
        print(
            f"Deleted empty docs! {doc_deletion_count}/{doc_process_count} documents were empty."
        )
    except Exception as e:
        print(e)
    return


@admin.action(description="(latest year) Populate Aims and Context")
def populate_aims_and_context(model_admin, req, selected):
    if len(selected) != 1:
        print("PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS")
        return

    try:
        sections_to_populate = [
            "aims",
            "context",
        ]

        # Get Annual reports and sort by year (highest year comes first) to get latest year and eligible reports
        latest_year = AnnualReport.objects.aggregate(latest_year=Max("year"))[
            "latest_year"
        ]
        eligible_prs = ProgressReport.objects.filter(year=latest_year)
        updated_count = 0

        # Check each report/project to see if it can be populated, and populate each section if it can
        for pr in eligible_prs:
            all_prs_for_project = ProgressReport.objects.filter(
                project=pr.project
            ).order_by("-year")
            if all_prs_for_project.count() > 1:
                previous_data_object = all_prs_for_project[1]
                # data_to_update = {}
                for section in sections_to_populate:
                    setattr(pr, section, getattr(previous_data_object, section))
                pr.save()
                updated_count += 1

        model_admin.message_user(
            req,
            f"Successfully populated aims and context for {updated_count} progress reports.",
        )
    except Exception as e:
        print(f"ERROR: {e}")

    return


# endregion ========================================================================================================


# region Admin ========================================================================================================
@admin.register(AnnualReport)
class AnnualReportAdmin(admin.ModelAdmin):
    list_display = ("pk", "year", "is_published", "pdf_generation_in_progress", "pdf")

    ordering = ["year"]


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "project",
        "display_year",
        "kind",
        "status",
        "pdf",
    )

    def display_year(self, obj):
        return obj.created_at.year

    display_year.short_description = "Created Year"

    class YearFilter(admin.SimpleListFilter):
        title = "Year"
        parameter_name = "year"

        def lookups(self, request, model_admin):
            # Get distinct years from the model
            years = (
                model_admin.model.objects.values_list("created_at__year", flat=True)
                .order_by("-created_at__year")
                .distinct()
            )
            # Convert the years to string values
            return [(str(year), str(year)) for year in years]

        def queryset(self, request, queryset):
            if self.value():
                # Filter queryset based on the selected year
                year = int(self.value())
                queryset = queryset.filter(created_at__year=year)
            return queryset

    list_filter = (
        "pdf_generation_in_progress",
        YearFilter,
        "kind",
        "status",
    )

    search_fields = ["project__title"]

    # Orders based on year (lastest year first)
    ordering = ["-created_at__year"]

    actions = [
        delete_unlinked_docs,
        provide_final_approval_for_docs_if_next_exist,
    ]


@admin.register(ConceptPlan)
class ConceptPlanAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "doc_status",
        "document",
    )

    list_filter = ("document__created_at",)

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"


@admin.register(ProjectPlan)
class ProjectPlanAdmin(admin.ModelAdmin):
    list_display = ("pk", "doc_status", "document")

    list_filter = ("document__created_at",)

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"


@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ("pk", "doc_status", "document")

    list_filter = ("document__created_at", "year")

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"
    actions = [populate_aims_and_context]


@admin.register(StudentReport)
class StudentReportAdmin(admin.ModelAdmin):
    list_display = ("pk", "doc_status", "document")

    list_filter = ("document__created_at",)

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"


@admin.register(ProjectClosure)
class ProjectClosureAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "doc_created_data",
        "doc_status",
        "document",
    )

    list_filter = ("document__created_at",)

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_created_data(self, obj):
        return obj.document.created_at

    doc_created_data.short_description = "Created At"

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"


@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):

    list_display = (
        "pk",
        "project_plan",
        "ae_endorsement_required",
        "ae_endorsement_provided",
        "display_data_management",
        "no_specimens",
    )

    def display_data_management(self, obj):
        if obj.data_management:
            return (
                obj.data_management[:100] + "..."
                if len(obj.data_management) > 100
                else obj.data_management
            )
        return None

    display_data_management.short_description = "Data Management"

    list_filter = (
        "ae_endorsement_required",
        "ae_endorsement_provided",
    )

    search_fields = [
        "data_management",
        "no_specimens",
        "project_plan__document__project__title",
    ]


# endregion ========================================================================================================
