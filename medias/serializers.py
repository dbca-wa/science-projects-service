# region Imports ===================================

import base64
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)

from agencies.serializers import TinyBusinessAreaSerializer
from .models import (
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    LegacyAnnualReportPDF,
    ProjectDocumentPDF,
    ProjectPlanMethodologyPhoto,
    UserAvatar,
    AgencyImage,
    ProjectPhoto,
    AECEndorsementPDF,
)

# endregion Imports ===================================


# region Project Doc Media Serializers ===================================


class ProjectDocumentPDFSerializer(ModelSerializer):
    class Meta:
        model = ProjectDocumentPDF
        fields = [
            "id",
            "file",
            "document",
            "project",
        ]


class ProjectDocumentPDFCreationSerializer(ModelSerializer):
    class Meta:
        model = ProjectDocumentPDF
        fields = "__all__"


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


class TinyMethodologyImageSerializer(ModelSerializer):
    project_plan = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectPlanMethodologyPhoto
        fields = [
            "id",
            "file",
            "project_plan",
            "uploader",
        ]

    def get_project_plan(self, obj):
        project_plan = obj.project_plan
        if project_plan:
            return {
                "id": project_plan.id,
            }

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


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
            }

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }


# endregion  ===================================


# region Annual Report Media Serializers ===================================


class TinyAnnualReportMediaSerializer(ModelSerializer):
    report = SerializerMethodField(read_only=True)

    class Meta:
        model = AnnualReportMedia
        fields = [
            "id",
            "kind",
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


class TinyAnnualReportPDFSerializer(ModelSerializer):
    report = SerializerMethodField(read_only=True)

    class Meta:
        model = AnnualReportPDF
        fields = [
            "id",
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


class TinyLegacyAnnualReportPDFSerializer(ModelSerializer):
    report = SerializerMethodField()

    class Meta:
        model = LegacyAnnualReportPDF
        fields = [
            "id",
            "file",
            "year",
            "report",
        ]

    def get_report(self, obj):
        return {
            "id": 0,
            "year": obj.year,
        }


class AnnualReportPDFCreateSerializer(ModelSerializer):

    class Meta:
        model = AnnualReportPDF
        fields = "__all__"

    def create(self, validated_data):
        arp = AnnualReportPDF.objects.create(**validated_data)
        return arp


class LegacyAnnualReportPDFCreateSerializer(ModelSerializer):

    class Meta:
        model = LegacyAnnualReportPDF
        fields = "__all__"

    def create(self, validated_data):
        arp = LegacyAnnualReportPDF.objects.create(**validated_data)
        return arp


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
            try:
                with open(obj.file.path, "rb") as file:
                    pdf_data = file.read()
                    return base64.b64encode(pdf_data).decode("utf-8")
            except FileNotFoundError:
                return None

        return None


class LegacyAnnualReportPDFSerializer(ModelSerializer):
    pdf_data = SerializerMethodField(read_only=True)

    class Meta:
        model = LegacyAnnualReportPDF
        fields = "__all__"

    def get_pdf_data(self, obj):
        if obj.file:
            with open(obj.file.path, "rb") as file:
                pdf_data = file.read()
                return base64.b64encode(pdf_data).decode("utf-8")

        return None


# endregion  ===================================


# region Business Area Photo Serializers ===================================


class TinyBusinessAreaPhotoSerializer(ModelSerializer):
    business_area = TinyBusinessAreaSerializer(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = BusinessAreaPhoto
        fields = [
            "id",
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


class BusinessAreaPhotoCreateSerializer(ModelSerializer):
    """Serializer for creating business area photos"""
    class Meta:
        model = BusinessAreaPhoto
        fields = "__all__"


# endregion  ===================================


# region Project Photo Serializers ===================================


class TinyProjectPhotoSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectPhoto
        fields = [
            "id",
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
        return None  # Add explicit return for None case

    def get_uploader(self, obj):
        uploader = obj.uploader
        if uploader:
            return {
                "id": uploader.id,
                "username": uploader.username,
            }
        return None  # Add explicit return for None case


class ProjectPhotoSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    uploader = SerializerMethodField(read_only=True)

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


class ProjectPhotoCreateSerializer(ModelSerializer):
    """Serializer for creating project photos"""
    class Meta:
        model = ProjectPhoto
        fields = "__all__"


# endregion ===================================


# region Agency Photo Serializers ===================================


class TinyAgencyPhotoSerializer(ModelSerializer):
    agency = SerializerMethodField(read_only=True)
    file = SerializerMethodField()

    class Meta:
        model = AgencyImage
        fields = [
            "id",
            "file",
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


class AgencyPhotoSerializer(ModelSerializer):
    agency = SerializerMethodField(read_only=True)
    file = SerializerMethodField()

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


class AgencyPhotoCreateSerializer(ModelSerializer):
    """Serializer for creating agency photos"""
    class Meta:
        model = AgencyImage
        fields = "__all__"


# endregion  ===================================


# region User Avatar Serializers ===================================


class TinyUserAvatarSerializer(ModelSerializer):
    user = SerializerMethodField(read_only=True)

    class Meta:
        model = UserAvatar
        fields = [
            "id",
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


class UserAvatarCreateSerializer(ModelSerializer):
    """Serializer for creating user avatars"""
    class Meta:
        model = UserAvatar
        fields = "__all__"


class StaffProfileAvatarSerializer(ModelSerializer):
    user = SerializerMethodField(read_only=True)

    class Meta:
        model = UserAvatar
        fields = [
            "id",
            "file",
            "user",
        ]

    def get_user(self, obj):
        user = obj.user
        if user:
            return {
                "id": user.id,
            }


# endregion  ===================================
