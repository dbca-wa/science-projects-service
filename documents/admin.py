import ast
from django.contrib import admin

from users.serializers import TinyUserSerializer
from .models import (
    AnnualReport,
    ProjectDocument,
    ConceptPlan,
    ProjectPlan,
    Endorsement,
    ProgressReport,
    StudentReport,
    ProjectClosure,
    Publication,
)
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.db.models import Max


@admin.register(AnnualReport)
class AnnualReportAdmin(admin.ModelAdmin):
    list_display = ("pk", "year", "is_published", "pdf_generation_in_progress", "pdf")

    ordering = ["year"]


@admin.action(description="(Concept Plans) Provide all approvals if Next Doc exists")
def provide_final_approval_for_concepts_where_projectplans_exist(
    model_admin, req, selected
):
    if len(selected) != 1:
        print("PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS")
        return


@admin.action(description="(Project Plans) Provide all approvals if Next Doc exists")
def provide_final_approval_for_projectplans_where_progressreports_exist(
    model_admin, req, selected
):
    if len(selected) != 1:
        print("PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS")
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

    actions = [delete_unlinked_docs]


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
        # "bm_endorsement_required",
        # "hc_endorsement_required",
        "ae_endorsement_required",
        # "dm_endorsement_required",
        # "bm_endorsement_provided",
        # "hc_endorsement_provided",
        "ae_endorsement_provided",
        # "dm_endorsement_provided",
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
        # "bm_endorsement_required",
        # "hc_endorsement_required",
        "ae_endorsement_required",
        # "dm_endorsement_required",
        # "bm_endorsement_provided",
        # "hc_endorsement_provided",
        "ae_endorsement_provided",
        # "dm_endorsement_provided",
    )

    search_fields = [
        "data_management",
        "no_specimens",
        "project_plan__document__project__title",
    ]


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


class PublicationForm(forms.ModelForm):
    User = get_user_model()
    internal_authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by("first_name"),
        widget=UserFilterWidget("Internal Authors", is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.initial["internal_authors"] = list(
                instance.internal_authors.values_list("id", flat=True)
            )

        self.fields["internal_authors"].queryset = User.objects.all().order_by(
            "first_name"
        )

    class Meta:
        model = Publication
        fields = "__all__"


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "title",
        "year",
        "kind",
        "doi",
        "apa_citation",
    )
    form = PublicationForm

    def apa_citation(self, obj):
        return obj.get_apa_citation()

    apa_citation.short_description = "APA Citation"

    list_filter = ("kind",)

    search_fields = ["title"]

    ordering = ["-created_at"]
