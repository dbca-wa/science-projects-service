from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ImageField,
)

from agencies.serializers import TinyBusinessAreaSerializer

# from documents.serializers import AnnualReportSerializer
from .models import (
    AnnualReportMedia,
    BusinessAreaPhoto,
    ProjectDocumentPDF,
    UserAvatar,
    AgencyImage,
    ProjectPhoto,
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


class TinyBusinessAreaPhotoSerializer(ModelSerializer):
    business_area = TinyBusinessAreaSerializer(read_only=True)
    uploader = SerializerMethodField(read_only=True)

    class Meta:
        model = BusinessAreaPhoto
        fields = [
            "pk",
            # "old_file",
            "file",
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
