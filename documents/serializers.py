# region Imports ===================================
from calendar import c
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from common.utils import TeamMemberMixin

from medias.models import ProjectDocumentPDF, ProjectPlanMethodologyPhoto
from projects.models import Project, ProjectArea, ProjectMember
from projects.serializers import (
    MiniProjectMemberSerializer,
    ProjectAreaSerializer,
    TinyProjectSerializer,
    TinyStudentProjectARSerializer,
)
from .models import (
    ConceptPlan,
    CustomPublication,
    ProjectPlan,
    ProgressReport,
    StudentReport,
    ProjectClosure,
    Endorsement,
    ProjectDocument,
    AnnualReport,
)
from medias.serializers import (
    AECPDFSerializer,
    ProjectDocumentPDFSerializer,
    TinyAnnualReportMediaSerializer,
    AnnualReportMediaSerializer,
    TinyAnnualReportPDFSerializer,
    TinyMethodologyImageSerializer,
)

# endregion  ===================================


# region AR Serializers ===================================
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
            "is_published",
        ]


class MiniAnnualReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualReport
        fields = [
            "pk",
            "year",
            "pdf_generation_in_progress",
        ]


class AnnualReportSerializer(serializers.ModelSerializer):
    media = AnnualReportMediaSerializer(many=True, read_only=True, source="media.all")

    class Meta:
        model = AnnualReport
        fields = "__all__"


# endregion  ===================================


# region Project Document & Endorsement Serializers ===================================
class MidDocumentSerializer(serializers.ModelSerializer):
    project = TinyProjectSerializer(read_only=True)
    referenced_doc = serializers.SerializerMethodField()

    def get_referenced_doc(self, obj):
        if obj.kind == "concept":
            doc = ConceptPlan.objects.filter(document=obj.document)
        elif obj.kind == "projectplan":
            doc = ProjectPlan.objects.filter(document=obj.document)
        elif obj.kind == "progressreport":
            doc = ProgressReport.objects.filter(document=obj.document)
        elif obj.kind == "studentreport":
            doc = StudentReport.objects.filter(document=obj.document)
        elif obj.kind == "projectclosure":
            doc = ProjectClosure.objects.filter(document=obj.document)
        else:
            print("ERROR ON OBJ KIND FOR MIDDOCUMENTSERIALIZER", obj.kind)
            raise NotFound
        return doc

    class Meta:
        model = ProjectDocument
        fields = [
            "pk",
            "kind",
            "project",
            "referenced_doc",
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


class TinyProjectDocumentSerializerWithUserDocsBelongTo(serializers.ModelSerializer):
    project = TinyProjectSerializer(read_only=True)
    created_year = serializers.SerializerMethodField()
    pdf = ProjectDocumentPDFSerializer(read_only=True)  # Include the PDF serializer
    for_user = serializers.SerializerMethodField()

    def get_created_year(self, obj):
        return obj.created_at.year

    def get_for_user(self, obj):
        # Retrieve the user from the serializer context
        user = self.context.get("for_user", None)
        if user:

            # Safely get the user's avatar
            avatar = getattr(user, "avatar", None)

            print(avatar)
            image_url = avatar.file.url if avatar else None

            return {
                "pk": user.pk,
                "email": user.email,
                "display_first_name": user.display_first_name,
                "display_last_name": user.display_last_name,
                "image": image_url,
            }
        return None

    class Meta:
        model = ProjectDocument
        fields = [
            "pk",
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
            "for_user",
        ]


class TinyProjectDocumentARSerializer(serializers.ModelSerializer):
    project = TinyProjectSerializer(read_only=True)
    created_year = serializers.SerializerMethodField()
    pdf = ProjectDocumentPDFSerializer(read_only=True)  # Include the PDF serializer
    area = ProjectAreaSerializer(read_only=True)

    def get_created_year(self, obj):
        return obj.created_at.year

    class Meta:
        model = ProjectDocument
        fields = [
            "pk",
            "created_at",
            "updated_at",
            "creator",
            "modifier",
            "created_year",
            "kind",
            "status",
            "project",
            "area",
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
            "year",
            "number",
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


class ProjectPlanSerializer(serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer()
    endorsements = serializers.SerializerMethodField(
        read_only=True,
        source="documents.Endorsement",
    )
    methodology_image = serializers.SerializerMethodField(
        read_only=True,
        source="medias.ProjectPlanMethodologyPhoto",
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
            "methodology_image",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]

    def get_endorsements(self, obj):
        print(obj)
        project_plan = obj
        endorsements = Endorsement.objects.get(project_plan=project_plan)
        return EndorsementSerializerForProjectPlanView(endorsements).data

    def get_methodology_image(self, obj):
        print(obj)
        project_plan = obj
        try:
            image = ProjectPlanMethodologyPhoto.objects.get(project_plan=project_plan)
        except ProjectPlanMethodologyPhoto.DoesNotExist:
            return None
        return TinyMethodologyImageSerializer(image).data


class TinySReportARProjectDocumentSerializer(serializers.ModelSerializer):
    project = TinyStudentProjectARSerializer(read_only=True)
    created_year = serializers.SerializerMethodField()
    pdf = ProjectDocumentPDFSerializer(read_only=True)  # Include the PDF serializer

    def get_created_year(self, obj):
        return obj.created_at.year

    class Meta:
        model = ProjectDocument
        fields = [
            "pk",
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


class StudentReportAnnualReportSerializer(TeamMemberMixin, serializers.ModelSerializer):
    document = TinySReportARProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    team_members = serializers.SerializerMethodField()
    project_areas = serializers.SerializerMethodField()

    def get_project_areas(self, student_report):
        project = student_report.project
        try:
            areas = ProjectArea.objects.filter(project=project.pk).first()
            ser = ProjectAreaSerializer(areas)
        except ProjectArea.DoesNotExist:
            print(f"error on area/ser (not found for project: {project.title})")
            raise NotFound
        else:
            return ser

    class Meta:
        model = StudentReport
        fields = [
            "pk",
            "document",
            # "project",
            "report",
            "year",
            "progress_report",
            "team_members",
            "project_areas",
        ]


class ProgressReportAnnualReportSerializer(
    TeamMemberMixin, serializers.ModelSerializer
):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    team_members = serializers.SerializerMethodField()
    project_areas = serializers.SerializerMethodField()

    def get_project_areas(self, student_report):
        project = student_report.project
        try:
            areas = ProjectArea.objects.filter(project=project.pk).first()
            ser = ProjectAreaSerializer(areas)
        except ProjectArea.DoesNotExist:
            print(f"error on area/ser (not found for project: {project.title})")
            raise NotFound
        else:
            return ser

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
            "team_members",
            "project_areas",
        ]


class ProgressReportSerializer(TeamMemberMixin, serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    team_members = serializers.SerializerMethodField()

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
            "team_members",
        ]


class StudentReportSerializer(TeamMemberMixin, serializers.ModelSerializer):
    document = TinyProjectDocumentSerializer(read_only=True)
    report = TinyAnnualReportSerializer(read_only=True)
    team_members = serializers.SerializerMethodField()

    class Meta:
        model = StudentReport
        fields = [
            "pk",
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


# endregion  ===================================


# region Publication Serializers ===================================


class CustomPublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPublication
        fields = ["pk", "public_profile", "title", "year"]


class PublicationDocSerializer(serializers.Serializer):
    DocId = serializers.CharField(allow_blank=True, required=False, default="")
    BiblioText = serializers.CharField(allow_blank=True, required=False, default="")
    staff_only = serializers.BooleanField(required=False, default=False)
    UserName = serializers.CharField(allow_blank=True, required=False, default="")
    recno = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.ListField(
        child=serializers.CharField(allow_blank=True, required=False),
        required=False,
        default=list,
    )
    title = serializers.CharField(allow_blank=True, required=False, default="")
    Material = serializers.CharField(allow_blank=True, required=False, default="")
    publisher = serializers.CharField(allow_blank=True, required=False, default="")
    AuthorBiblio = serializers.CharField(allow_blank=True, required=False, default="")
    year = serializers.CharField(allow_blank=True, required=False, default="")
    documentKey = serializers.CharField(allow_blank=True, required=False, default="")
    UserId = serializers.CharField(allow_blank=True, required=False, default="")
    author = serializers.CharField(allow_blank=True, required=False, default="")
    citation = serializers.CharField(allow_blank=True, required=False, default="")
    place = serializers.CharField(allow_blank=True, required=False, default="")
    BiblioEditors = serializers.CharField(allow_blank=True, required=False, default="")
    link_address = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False, default=list
    )
    link_category = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False, default=list
    )
    link_notes = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False, default=list
    )


class LibraryPublicationResponseSerializer(serializers.Serializer):
    numFound = serializers.IntegerField(required=False, default=0)
    start = serializers.IntegerField(required=False, default=0)
    numFoundExact = serializers.BooleanField(required=False, default=True)
    docs = PublicationDocSerializer(many=True, required=False, default=list)
    isError = serializers.BooleanField(required=False, default=False)
    errorMessage = serializers.CharField(required=False, default="", allow_blank=True)


class PublicationResponseSerializer(serializers.Serializer):
    staffProfilePk = serializers.IntegerField()
    libraryData = LibraryPublicationResponseSerializer()
    customPublications = CustomPublicationSerializer(many=True)


# endregion  ===================================
