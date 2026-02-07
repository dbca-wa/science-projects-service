"""
Project export serializers (for annual reports and data tables)
"""

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from agencies.serializers import TinyBusinessAreaSerializer
from common.utils import ProjectTeamMemberMixin
from documents.templatetags.custom_filters import extract_text_content
from medias.serializers import ProjectPhotoSerializer, TinyProjectPhotoSerializer

from ..models import Project


class ARProjectSerializer(ModelSerializer):
    """Annual report project serializer"""

    image = ProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    team_members = SerializerMethodField

    class Meta:
        model = Project
        fields = "__all__"


class ARExternalProjectSerializer(ProjectTeamMemberMixin, ModelSerializer):
    """Annual report external project serializer"""

    team_members = SerializerMethodField()
    partners = SerializerMethodField()
    funding = SerializerMethodField()

    def get_partners(self, project):
        try:
            ext = project.external_project_info
            return ext.collaboration_with
        except Exception:
            print(
                "\nEXCEPTION (NO PARTNERS):",
                extract_text_content(project.title),
            )
            return ""

    def get_funding(self, project):
        try:
            ext = project.external_project_info
            return ext.budget
        except Exception:
            print(
                "\nEXCEPTION (NO FUNDING):",
                extract_text_content(project.title),
            )
            return ""

    class Meta:
        model = Project
        fields = "__all__"


class TinyStudentProjectARSerializer(ModelSerializer):
    """Tiny student project serializer for annual reports"""

    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    student_level = SerializerMethodField()

    def get_student_level(self, project):
        return project.student_project_info.level

    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "status",
            "kind",
            "year",
            "number",
            "business_area",
            "image",
            "student_level",
            "start_date",
            "end_date",
        )


class ProjectDataTableSerializer(ModelSerializer):
    """Project serializer for data tables"""

    image = ProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    role = SerializerMethodField()
    tag = SerializerMethodField()
    description = SerializerMethodField()
    start_date = SerializerMethodField()
    end_date = SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "role",
            "tag",
            "image",
            "kind",
            "created_at",
            "status",
            "business_area",
            "description",
            "start_date",
            "end_date",
        ]

    def get_start_date(self, obj):
        if obj.start_date:
            return obj.start_date.year
        return None

    def get_end_date(self, obj):
        if obj.end_date:
            return obj.end_date.year
        return None

    def get_role(self, obj):
        projects_with_roles = self.context.get("projects_with_roles", [])
        role = next(
            (role for project, role in projects_with_roles if project.id == obj.id),
            None,
        )
        return role

    def get_tag(self, obj):
        return obj.get_project_tag()

    def get_description(self, obj):
        return obj.get_description()
