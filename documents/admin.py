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


@admin.register(AnnualReport)
class AnnualReportAdmin(admin.ModelAdmin):
    list_display = ("pk", "year", "is_published")

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
        YearFilter,
        "kind",
        "status",
    )

    search_fields = ["project__title"]

    # Orders based on year (lastest year first)
    ordering = ["-created_at__year"]


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

    list_filter = ("document__created_at",)

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"


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
    list_display = ("pk", "doc_status", "document")

    list_filter = ("document__created_at",)

    search_fields = ["document__project__title"]

    ordering = ["-document__created_at"]

    def doc_status(self, obj):
        return obj.document.get_status_display()

    doc_status.short_description = "Document Status"


@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "project_plan",
        "bm_endorsement_required",
        "hc_endorsement_required",
        "ae_endorsement_required",
        "dm_endorsement_required",
        "bm_endorsement_provided",
        "hc_endorsement_provided",
        "ae_endorsement_provided",
        "dm_endorsement_provided",
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
        "bm_endorsement_required",
        "hc_endorsement_required",
        "ae_endorsement_required",
        "dm_endorsement_required",
        "bm_endorsement_provided",
        "hc_endorsement_provided",
        "ae_endorsement_provided",
        "dm_endorsement_provided",
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
            print(instance)
            print(instance.internal_authors.values_list("id", flat=True))
            print(list(instance.internal_authors.values_list("id", flat=True)))
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
