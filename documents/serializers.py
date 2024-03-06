from medias.models import ProjectDocumentPDF
from projects.models import Project, ProjectMember
from projects.serializers import (
    MiniProjectMemberSerializer,
    ProjectSerializer,
    TinyProjectMemberSerializer,
    TinyProjectSerializer,
)
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
    AECPDFSerializer,
    ProjectDocumentPDFSerializer,
    TinyAnnualReportMediaSerializer,
    AnnualReportMediaSerializer,
    TinyAnnualReportPDFSerializer,
)

from rest_framework import serializers
from rest_framework.exceptions import NotFound


class TinyAnnualReportSerializer(serializers.ModelSerializer):
    media = TinyAnnualReportMediaSerializer(
        many=True, read_only=True, source="media.all"
    )
    pdf = TinyAnnualReportPDFSerializer(read_only=True)

    class Meta:
        model = AnnualReport
        fields = [
            "pk",
            "year",
            "creator",
            "date_open",
            "date_closed",
            "media",
            "pdf",
            "pdf_generation_in_progress",
        ]


class MiniAnnualReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualReport
        fields = [
            "pk",
            "year",
            "pdf_generation_in_progress",
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


class SuperSmallProjSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = [
            "pk",
            "title",
            "kind",
        ]


class SuperSmallDocSerializer(serializers.ModelSerializer):

    project = SuperSmallProjSerializer(read_only=True)

    class Meta:
        model = ProjectDocument
        fields = [
            "pk",
            "project",
        ]


class TinyProjectPlanSerializer(serializers.ModelSerializer):

    document = SuperSmallDocSerializer(read_only=True)

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
            # "involves_plants",
            # "involves_animals",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]


class MiniEndorsementSerializer(serializers.ModelSerializer):
    project_plan = TinyProjectPlanSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = [
            "pk",
            "project_plan",
        ]


class TinyEndorsementSerializer(serializers.ModelSerializer):
    project_plan = TinyProjectPlanSerializer(read_only=True)
    aec_pdf = AECPDFSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = [
            "pk",
            "project_plan",
            # "bm_endorsement_required",
            # "hc_endorsement_required",
            # "bm_endorsement_provided",
            # "hc_endorsement_provided",
            "ae_endorsement_required",
            "ae_endorsement_provided",
            "aec_pdf",
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
        projdoc = ProjectDocument.objects.create(**validated_data)
        return projdoc


class ProjectDocPDFFileDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocumentPDF
        fields = ("file",)


class ProjectDocumentSerializer(serializers.ModelSerializer):

    project = TinyProjectSerializer(read_only=True)
    pdf = ProjectDocPDFFileDisplaySerializer(required=False)

    class Meta:
        model = ProjectDocument
        fields = "__all__"


class ConceptPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptPlan
        fields = "__all__"
        # fields = [
        #     "document",
        #     "background",
        #     "aims",
        #     "outcome",
        #     "collaborations",
        #     "strategic_context",
        #     "staff_time_allocation",
        #     "budget",
        # ]

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        concept_plan = ConceptPlan.objects.create(**validated_data)
        return concept_plan


class ProgressReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressReport
        fields = "__all__"

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        progress_report = ProgressReport.objects.create(**validated_data)
        return progress_report

    # class Meta:
    #     model = ProgressReport
    #     fields = [
    #         "document",
    #         "report",
    #         "year",
    #         "is_final_report",
    #         "context",
    #         "aims",
    #         "progress",
    #         "implications",
    #         "future",
    #     ]


class ProgressReportSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProgressReport
        fields = [
            "pk",
            "document",
            "project",
            "report",
            "year",
            "is_final_report",
            "context",
            "aims",
            "progress",
            "implications",
            "future",
        ]


class ProjectClosureCreationSerializer(serializers.ModelSerializer):
    # class Meta:
    #     model = ProjectClosure
    #     fields = [
    #         "document",
    #         "project",
    #         "intended_outcome",
    #         "reason",
    #         "scientific_outputs",
    #         "knowledge_transfer",
    #         "data_location",
    #         "hardcopy_location",
    #         "backup_location",
    #     ]
    class Meta:
        model = ProjectClosure
        fields = "__all__"

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        project_closure = ProjectClosure.objects.create(**validated_data)
        return project_closure


class ProjectPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPlan
        fields = "__all__"

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        project_plan = ProjectPlan.objects.create(**validated_data)
        return project_plan


class EndorsementSerializerForProjectPlanView(serializers.ModelSerializer):
    aec_pdf = AECPDFSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = [
            "pk",
            "ae_endorsement_provided",
            "ae_endorsement_required",
            # "bm_endorsement_required",
            # "hc_endorsement_required",
            # "dm_endorsement_required",
            # "bm_endorsement_provided",
            # "hc_endorsement_provided",
            # "dm_endorsement_provided",
            "data_management",
            "no_specimens",
            "aec_pdf",
        ]


class ConceptPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptPlan
        fields = "__all__"

    def create(self, validated_data):
        # Create a new ConceptPlan with the provided document primary key
        cp = ConceptPlan.objects.create(**validated_data)
        return cp


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


class StudentReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentReport
        fields = "__all__"


class ConceptPlanSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer()
    # project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ConceptPlan
        fields = [
            "pk",
            "document",
            # "project",
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]


class ProjectPlanSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer()
    # endorsements = EndorsementSerializerForProjectPlanView(read_only=True)

    endorsements = serializers.SerializerMethodField(
        read_only=True, source="documents.Endorsement"
    )
    # project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectPlan
        fields = [
            "pk",
            "document",
            # "project",
            "endorsements",
            "background",
            "project_tasks",
            "methodology",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            # "involves_plants",
            # "involves_animals",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]

    def get_endorsements(self, obj):
        print(obj)
        project_plan = obj
        endorsements = Endorsement.objects.get(project_plan=project_plan)
        return EndorsementSerializerForProjectPlanView(endorsements).data


class ProgressReportSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    # project = TinyProjectSerializer(read_only=True)
    team_members = serializers.SerializerMethodField()

    def get_team_members(self, student_report):
        # print('getting team')
        project = student_report.project
        try:
            members = ProjectMember.objects.filter(project=project.pk).all()
            serialized_members = []
            for member in members:
                ser = MiniProjectMemberSerializer(member)
                serialized_members.append(ser.data)
        except ProjectMember.DoesNotExist:
            print("error on team")
            raise NotFound
        else:
            return serialized_members

    class Meta:
        model = ProgressReport
        fields = [
            "pk",
            "document",
            # "project",
            "report",
            "year",
            "is_final_report",
            "context",
            "aims",
            "progress",
            "implications",
            "future",
            "team_members",
        ]


class StudentReportSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    # project = TinyProjectSerializer(read_only=True)
    team_members = serializers.SerializerMethodField()

    def get_team_members(self, student_report):
        # print('getting team')
        project = student_report.project
        try:
            members = ProjectMember.objects.filter(project=project.pk).all()
            serialized_members = []
            for member in members:
                ser = MiniProjectMemberSerializer(member)
                serialized_members.append(ser.data)
        except ProjectMember.DoesNotExist:
            print("error on team")
            raise NotFound
        else:
            return serialized_members

    class Meta:
        model = StudentReport
        fields = [
            "pk",
            # "project",
            "document",
            "report",
            "progress_report",
            "year",
            "team_members",
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
