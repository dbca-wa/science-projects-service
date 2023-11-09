from projects.serializers import ProjectSerializer, TinyProjectSerializer
from users.serializers import TinyUserSerializer
from .models import (
    ConceptPlan,
    ProjectPlan,
    ProgressReport,
    StudentReport,
    ProjectClosure,
    Endorsement,
    ProjectDocument,
    Publication,
    AnnualReport,
)
from medias.serializers import (
    ProjectDocumentPDFSerializer,
    TinyAnnualReportMediaSerializer,
    AnnualReportMediaSerializer,
)

from rest_framework import serializers


class TinyAnnualReportSerializer(serializers.ModelSerializer):
    media = TinyAnnualReportMediaSerializer(
        many=True, read_only=True, source="media.all"
    )

    class Meta:
        model = AnnualReport
        fields = [
            "pk",
            "year",
            "creator",
            "date_open",
            "date_closed",
            "media",
        ]


class TinyProjectDocumentSerializer(serializers.ModelSerializer):
    project = TinyProjectSerializer(read_only=True)
    created_year = serializers.SerializerMethodField()
    pdf = ProjectDocumentPDFSerializer(read_only=True)  # Include the PDF serializer

    def get_created_year(self, obj):
        return obj.created_at.year

    class Meta:
        model = ProjectDocument
        fields = [
            "pk",
            # "document",
            "created_at",
            "updated_at",
            "creator",
            "modifier",
            "created_year",
            "kind",
            "status",
            "project",
            "project_lead_approval_granted",
            "business_area_lead_approval_granted",
            "directorate_approval_granted",
            "pdf",
            "pdf_generation_in_progress",
        ]


class TinyConceptPlanSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer()

    class Meta:
        model = ConceptPlan
        fields = [
            "pk",
            "document",
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]


class TinyProjectPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPlan
        fields = [
            "pk",
            "document",
            "background",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "involves_plants",
            "involves_animals",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]


class TinyEndorsementSerializer(serializers.ModelSerializer):
    project_plan = TinyProjectPlanSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = [
            "pk",
            "project_plan",
            "bm_endorsement",
            "hc_endorsement",
            "ae_endorsement",
            "data_manager_endorsement",
        ]


class TinyProgressReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressReport
        fields = [
            "pk",
            "document",
            "year",
            "is_final_report",
            "context",
            "aims",
            "progress",
            "implications",
            "future",
        ]


class TinyProjectClosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectClosure
        fields = [
            "pk",
            "document",
            "intended_outcome",
            "reason",
            "scientific_outputs",
            "knowledge_transfer",
            "data_location",
            "hardcopy_location",
            "backup_location",
        ]


class TinyStudentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentReport
        fields = [
            "pk",
            "document",
            "progress_report",
            "year",
        ]


class TinyPublicationSerializer(serializers.ModelSerializer):
    apa_citation = serializers.SerializerMethodField()

    def get_apa_citation(self, obj):
        return obj.get_apa_citation()

    class Meta:
        model = Publication
        fields = ["pk", "title", "kind", "year", "apa_citation"]


class PublicationSerializer(serializers.ModelSerializer):
    apa_citation = serializers.SerializerMethodField()
    internal_authors = TinyUserSerializer(many=True, read_only=True)

    def get_apa_citation(self, obj):
        return obj.get_apa_citation()

    class Meta:
        model = Publication
        fields = "__all__"


class AnnualReportSerializer(serializers.ModelSerializer):
    media = AnnualReportMediaSerializer(many=True, read_only=True, source="media.all")

    class Meta:
        model = AnnualReport
        fields = "__all__"


class ProjectDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = "__all__"

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        concept_plan = ProjectDocument.objects.create(**validated_data)
        return concept_plan


class ProjectDocumentSerializer(serializers.ModelSerializer):
    # details = serializers.Serializer()

    project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectDocument
        fields = "__all__"

    # def get_details(self, obj):
    #     kind = obj.kind

    #     if kind == "concept_plan":
    #         concept_plan_details = obj.concept_plan_details.first()
    #         if concept_plan_details:
    #             return TinyConceptPlanSerializer(
    #                 concept_plan_details, context=self.context
    #             ).data
    #     elif kind == "project_plan":
    #         project_plan_details = obj.project_plan_details.first()
    #         if project_plan_details:
    #             return TinyProjectPlanSerializer(
    #                 project_plan_details, context=self.context
    #             ).data
    #     elif kind == "progressreport":
    #         progress_report_details = obj.progress_report_details.first()
    #         if progress_report_details:
    #             return TinyProgressReportSerializer(
    #                 progress_report_details, context=self.context
    #             ).data
    #     elif kind == "studentreport":
    #         student_report_details = obj.student_report_details.first()
    #         if student_report_details:
    #             return TinyStudentReportSerializer(
    #                 student_report_details, context=self.context
    #             ).data
    #     elif kind == "projectclosure":
    #         project_closure_details = obj.project_closure_details.first()
    #         if project_closure_details:
    #             return TinyProjectClosureSerializer(
    #                 project_closure_details, context=self.context
    #             ).data

    #     return None


class ConceptPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptPlan
        fields = [
            "document",
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        concept_plan = ConceptPlan.objects.create(**validated_data)
        return concept_plan


class ConceptPlanSerializer(serializers.ModelSerializer):
    document = ProjectDocumentSerializer()

    class Meta:
        model = ConceptPlan
        fields = [
            "pk",
            "document",
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]


class ProjectClosureCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectClosure
        fields = [
            "document",
            "intended_outcome",
            "reason",
            "scientific_outputs",
            "knowledge_transfer",
            "data_location",
            "hardcopy_location",
            "backup_location",
        ]


class ProjectPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPlan
        fields = [
            "document",
            "background",
            "methodology",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "involves_plants",
            "involves_animals",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        project_plan = ProjectPlan.objects.create(**validated_data)
        return project_plan


class ProjectPlanSerializer(serializers.ModelSerializer):
    document = ProjectDocumentSerializer()
    # endorsements = EndorsementSerializerForProjectPlanView(read_only=True)

    endorsements = serializers.SerializerMethodField(
        read_only=True, source="documents.Endorsement"
    )

    class Meta:
        model = ProjectPlan
        fields = [
            "pk",
            "document",
            "endorsements",
            "background",
            "project_tasks",
            "methodology",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "involves_plants",
            "involves_animals",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]

    def get_endorsements(self, obj):
        project_plan = obj
        endorsements = Endorsement.objects.filter(project_plan=project_plan)
        return EndorsementSerializerForProjectPlanView(endorsements, many=True).data


class EndorsementSerializerForProjectPlanView(serializers.ModelSerializer):
    class Meta:
        model = Endorsement
        fields = [
            "pk",
            "bm_endorsement",
            "hc_endorsement",
            "ae_endorsement",
            "data_manager_endorsement",
            "data_management",
            "no_specimens",
        ]


class EndorsementCreationSerializer(serializers.ModelSerializer):
    # project_plan = TinyProjectPlanSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = "__all__"

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        endorsement = Endorsement.objects.create(**validated_data)
        return endorsement


class EndorsementSerializer(serializers.ModelSerializer):
    project_plan = TinyProjectPlanSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = "__all__"


class ProgressReportSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)

    class Meta:
        model = ProgressReport
        fields = [
            "pk",
            "document",
            "report",
            "year",
            "is_final_report",
            "context",
            "aims",
            "progress",
            "implications",
            "future",
        ]


class StudentReportSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)

    class Meta:
        model = StudentReport
        fields = [
            "pk",
            "document",
            "report",
            "progress_report",
            "year",
        ]


class ProjectClosureSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProjectClosure
        fields = [
            "pk",
            "document",
            "intended_outcome",
            "reason",
            "scientific_outputs",
            "knowledge_transfer",
            "data_location",
            "hardcopy_location",
            "backup_location",
        ]
