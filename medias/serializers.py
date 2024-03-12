import base64
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ImageField,
)

from agencies.serializers import TinyBusinessAreaSerializer

# from documents.serializers import AnnualReportSerializer
from .models import (
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    ProjectDocumentPDF,
    ProjectPlanMethodologyPhoto,
    UserAvatar,
    AgencyImage,
    ProjectPhoto,
    AECEndorsementPDF,
)

# from PIL import Image
# from io import BytesIO


class ProjectDocumentPDFSerializer(ModelSerializer):
    class Meta:
        model = ProjectDocumentPDF
        fields = [
            "pk",
            # "old_file",
            "file",
            "document",
            "project",
        ]


class ProjectDocumentPDFCreationSerializer(ModelSerializer):
    class Meta:
        model = ProjectDocumentPDF
        fields = "__all__"


class TinyAnnualReportMediaSerializer(ModelSerializer):
    report = SerializerMethodField(read_only=True)

    class Meta:
        model = AnnualReportMedia
        fields = [
            "pk",
            "kind",
            # "old_file",
            "file",
            "report",
        ]

    def get_report(self, obj):
        report = obj.report
        if report:
            return {
                "id": report.id,
                "year": report.year,
            }
        return None


class AnnualReportMediaSerializer(ModelSerializer):
    report = SerializerMethodField(read_only=True)

    class Meta:
        model = AnnualReportMedia
        fields = "__all__"

    def get_report(self, obj):
        report = obj.report
        if report:
            return {
                "id": report.id,
                "year": report.year,
            }
        return None


class AnnualReportMediaCreationSerializer(ModelSerializer):
    class Meta:
        model = AnnualReportMedia
        fields = "__all__"

    # def get_report(self, obj):
    #     report = obj.report
    #     if report:
    #         return {
    #             "id": report.id,
    #             "year": report.year,
    #         }
    #     return None


class TinyAnnualReportPDFSerializer(ModelSerializer):
    report = SerializerMethodField(read_only=True)

    class Meta:
        model = AnnualReportPDF
        fields = [
            "pk",
            # "old_file",
            "file",
            "report",
        ]

    def get_report(self, obj):
        report = obj.report
        if report:
            return {
                "id": report.id,
                "year": report.year,
            }
        return None


class AECPDFSerializer(ModelSerializer):
    class Meta:
        model = AECEndorsementPDF
        fields = "__all__"


class AECPDFCreateSerializer(ModelSerializer):
    class Meta:
        model = AECEndorsementPDF
        fields = "__all__"

    def create(self, validated_data):
        cp = AECEndorsementPDF.objects.create(**validated_data)
        return cp


class AnnualReportPDFCreateSerializer(ModelSerializer):
    # report = SerializerMethodField()

    class Meta:
        model = AnnualReportPDF
        fields = "__all__"

    def create(self, validated_data):
        cp = AnnualReportPDF.objects.create(**validated_data)
        return cp


class AnnualReportPDFSerializer(ModelSerializer):
    report = SerializerMethodField(read_only=True)
    pdf_data = SerializerMethodField(read_only=True)

    class Meta:
        model = AnnualReportPDF
        fields = "__all__"

    def get_report(self, obj):
        report = obj.report
        if report:
            return {
                "id": report.id,
                "year": report.year,
                "pdf_generation_in_progress": report.pdf_generation_in_progress,
            }
        return None

    def get_pdf_data(self, obj):
        if obj.file:
            with open(obj.file.path, "rb") as file:
                pdf_data = file.read()
                return base64.b64encode(pdf_data).decode("utf-8")

        return None


class TinyBusinessAreaPhotoSerializer(ModelSerializer):
    business_area = TinyBusinessAreaSerializer(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = BusinessAreaPhoto
        fields = [
            "pk",
            # "old_file",
            # "file",
            "business_area",
            "uploader",
        ]

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


class BusinessAreaPhotoSerializer(ModelSerializer):
    business_area = TinyBusinessAreaSerializer(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = BusinessAreaPhoto
        fields = "__all__"

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


class TinyProjectPhotoSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectPhoto
        fields = [
            "pk",
            # "old_file",
            "file",
            "project",
            "uploader",
        ]

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "id": project.id,
                "title": project.title,
            }

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


class TinyMethodologyImageSerializer(ModelSerializer):
    project_plan = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectPlanMethodologyPhoto
        fields = [
            "pk",
            # "old_file",
            "file",
            "project_plan",
            "uploader",
        ]

    def get_project_plan(self, obj):
        project_plan = obj.project_plan
        if project_plan:
            return {
                "id": project_plan.id,
                # "title": project_plan.title,
            }

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


class ProjectPhotoSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)
    # old_file = SerializerMethodField()

    class Meta:
        model = ProjectPhoto
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "id": project.id,
                "title": project.title,
            }

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }

    # def get_old_file(self, obj):
    #     old_file = obj.old_file
    #     # if old_file:
    #     return old_file


class MethodologyImageCreateSerializer(ModelSerializer):
    class Meta:
        model = ProjectPlanMethodologyPhoto
        fields = "__all__"


class MethodologyImageSerializer(ModelSerializer):
    project_plan = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectPlanMethodologyPhoto
        fields = "__all__"

    def get_project_plan(self, obj):
        project_plan = obj.project_plan
        if project_plan:
            return {
                "id": project_plan.id,
                # "title": project_plan.title,
            }

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


class TinyAgencyPhotoSerializer(ModelSerializer):
    agency = SerializerMethodField(read_only=True)
    file = SerializerMethodField()
    # old_file = SerializerMethodField()

    # file = ImageField(source="file", read_only=True)
    # old_file = ImageField(source="old_file", read_only=True)
    class Meta:
        model = AgencyImage
        fields = [
            "pk",
            "file",
            # "old_file",
            "agency",
        ]

    def get_agency(self, obj):
        agency = obj.agency
        if agency:
            return {
                "id": agency.id,
                "name": agency.name,
            }

    def get_file(self, obj):
        file = obj.file
        if file:
            return file.url

    # def get_old_file(self, obj):
    #     old_file = obj.old_file
    #     if old_file:
    #         return old_file.url


class AgencyPhotoSerializer(ModelSerializer):
    agency = SerializerMethodField(read_only=True)
    file = SerializerMethodField()
    # old_file = SerializerMethodField()
    # file = ImageField(source="file", read_only=True)
    # old_file = ImageField(source="old_file", read_only=True)

    class Meta:
        model = AgencyImage
        fields = "__all__"

    def get_agency(self, obj):
        agency = obj.agency
        if agency:
            return {
                "id": agency.id,
                "name": agency.name,
            }

    def get_file(self, obj):
        file = obj.file
        if file:
            return file.url

    # def get_old_file(self, obj):
    #     old_file = obj.old_file
    #     if old_file:
    #         return old_file.url


class TinyUserAvatarSerializer(ModelSerializer):
    user = SerializerMethodField(read_only=True)

    class Meta:
        model = UserAvatar
        fields = [
            "pk",
            "file",
            "user",
        ]

    def get_user(self, obj):
        user = obj.user
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }


class UserAvatarSerializer(ModelSerializer):
    user = SerializerMethodField(read_only=True)

    class Meta:
        model = UserAvatar
        fields = "__all__"

    def get_user(self, obj):
        user = obj.user
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }
