# region IMPORTS ==============================================

from rest_framework.exceptions import NotFound
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers

from agencies.models import BusinessArea
from agencies.serializers import (
    AffiliationSerializer,
    BusinessAreaNameViewSerializer,
    TinyBusinessAreaSerializer,
)
from documents.templatetags.custom_filters import extract_text_content
import locations
from locations.models import Area
from medias.serializers import ProjectPhotoSerializer, TinyProjectPhotoSerializer
from locations.serializers import TinyAreaSerializer
from users.models import User
from users.serializers import TinyUserSerializer
from .models import (
    ExternalProjectDetails,
    Project,
    ProjectArea,
    ProjectDetail,
    ProjectMember,
    StudentProjectDetails,
)

from common.utils import ProjectTeamMemberMixin

# endregion ==============================================


# region SERIALIZERS ==============================================
class CreateProjectSerializer(ModelSerializer):
    image = ProjectPhotoSerializer(read_only=True)

    class Meta:
        model = Project
        fields = "__all__"

    def to_representation(self, instance):
        # Get the serialized data from the parent class
        representation = super().to_representation(instance)

        # Check if the custom context key is present and use 'pk' instead of 'id'
        if self.context.get("use_pk_for_id"):
            representation["pk"] = representation.pop("id")

        return representation


class ARProjectSerializer(ModelSerializer):
    image = ProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    team_members = SerializerMethodField

    class Meta:
        model = Project
        fields = "__all__"

    def to_representation(self, instance):
        # Get the serialized data from the parent class
        representation = super().to_representation(instance)

        # Check if the custom context key is present and use 'pk' instead of 'id'
        if self.context.get("use_pk_for_id"):
            representation["pk"] = representation.pop("id")

        return representation


class ARExternalProjectSerializer(ProjectTeamMemberMixin, ModelSerializer):
    team_members = serializers.SerializerMethodField()
    partners = serializers.SerializerMethodField()
    funding = serializers.SerializerMethodField()

    def get_partners(self, project):
        try:
            ext = project.external_project_info
            return ext.collaboration_with
        except:
            print(
                "\nEXCEPTION (NO PARTNERS):",
                extract_text_content(project.title),
            )
            return ""

    def get_funding(self, project):
        try:
            ext = project.external_project_info
            return ext.budget
        except:
            print(
                "\nEXCEPTION (NO FUNDING):",
                extract_text_content(project.title),
            )
            return ""

    class Meta:
        model = Project
        fields = "__all__"

    def to_representation(self, instance):
        # Get the serialized data from the parent class
        representation = super().to_representation(instance)

        # Check if the custom context key is present and use 'pk' instead of 'id'
        if self.context.get("use_pk_for_id"):
            representation["pk"] = representation.pop("id")

        return representation


class ProblematicProjectSerializer(ModelSerializer):
    tag = serializers.SerializerMethodField()
    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = BusinessAreaNameViewSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "pk",
            "title",
            "tag",
            "image",
            "kind",
            "created_at",
            "status",
            "business_area",
        ]

    def get_tag(self, obj):
        return obj.get_project_tag()


class ProjectSerializer(ModelSerializer):
    image = ProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    deletion_request_id = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = "__all__"

    def get_deletion_request_id(self, instance):
        # Use the method defined on the Project model to get the deletion request ID
        return instance.get_deletion_request_id()

    def to_representation(self, instance):
        # Get the serialized data from the parent class
        representation = super().to_representation(instance)

        # Check if the custom context key is present and use 'pk' instead of 'id'
        if self.context.get("use_pk_for_id"):
            representation["pk"] = representation.pop("id")

        # If a deletion request exists, add the deletion request ID to the representation
        representation["deletion_request_id"] = self.get_deletion_request_id(instance)

        return representation

    def get_areas(self, instance):
        return instance.area.areas
        # return TinyAreaSerializer(areas).data


class ProjectBAUpdateSerializer(ModelSerializer):
    class Meta:
        model = BusinessArea


class ProjectUpdateSerializer(ModelSerializer):
    image = ProjectPhotoSerializer(read_only=True)

    class Meta:
        model = Project
        fields = "__all__"

    def to_representation(self, instance):
        # Get the serialized data from the parent class
        representation = super().to_representation(instance)

        # Check if the custom context key is present and use 'pk' instead of 'id'
        if self.context.get("use_pk_for_id"):
            representation["pk"] = representation.pop("id")

        return representation


class UserProfileProjectSerializer(ModelSerializer):
    tag = serializers.SerializerMethodField()
    image = TinyProjectPhotoSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["pk", "title", "tag", "image"]

    def get_tag(self, obj):
        return obj.get_project_tag()


class TinyProjectSerializer(ModelSerializer):
    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)

    class Meta:
        model = Project
        fields = (
            "pk",
            "title",
            "status",
            "kind",
            "year",
            "number",
            "business_area",
            "image",
        )


class TinyStudentProjectARSerializer(ModelSerializer):
    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    student_level = serializers.SerializerMethodField()

    def get_student_level(self, project):
        return project.student_project_info.level

    class Meta:
        model = Project
        fields = (
            "pk",
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


class ProjectAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectArea
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        areas = instance.areas  # List of area IDs

        # Fetch all areas in one query instead of individual lookups
        if areas:
            try:
                area_objects = Area.objects.filter(pk__in=areas)
                area_serializer = TinyAreaSerializer(area_objects, many=True)
                representation["areas"] = area_serializer.data
            except Area.DoesNotExist:
                representation["areas"] = []
        else:
            representation["areas"] = []

        return representation


class PkAndKindOnlyProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ["pk", "kind"]


class MiniUserSerializer(ModelSerializer):
    title = serializers.SerializerMethodField()
    affiliation = serializers.SerializerMethodField()
    caretakers = serializers.SerializerMethodField()

    def get_title(self, user):
        return user.profile.title

    def get_affiliation(self, user):
        if user.work and user.work.affiliation:
            affiliation_instance = user.work.affiliation
            affiliation_data = AffiliationSerializer(affiliation_instance).data
            return affiliation_data
        else:
            return None

    class Meta:
        model = User
        fields = [
            "pk",
            "display_first_name",
            "display_last_name",
            "email",
            "is_active",
            "is_staff",
            "title",
            "affiliation",
            "caretakers",
        ]

    def get_caretakers(self, obj):
        # Call the user model's get_caretakers method
        caretakers = obj.get_caretakers()
        # Set caretaker data using list comprehension
        caretakers_data = [
            {
                "pk": obj.caretaker.pk,
                "display_first_name": obj.caretaker.display_first_name,
                "display_last_name": obj.caretaker.display_last_name,
                "email": obj.caretaker.email,
            }
            for obj in caretakers
        ]
        # Return whatever data is available
        return caretakers_data


class MiniProjectMemberSerializer(ModelSerializer):
    user = MiniUserSerializer(read_only=True)
    project = PkAndKindOnlyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "user",
            "project",
            "role",
            "is_leader",
            "position",
        ]


class TinyProjectMemberSerializer(ModelSerializer):
    user = TinyUserSerializer(read_only=True)
    project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "pk",
            "user",
            "project",
            "is_leader",
            "role",
            "time_allocation",
            "position",
            "comments",
            "short_code",
            "project",
        ]


class ProjectDataTableSerializer(ModelSerializer):
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
            "pk",
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
        if obj.start_date:
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get("use_pk_for_id"):
            representation["pk"] = representation.pop("id")
        representation["role"] = self.get_role(instance)
        return representation


class ProjectMemberSerializer(ModelSerializer):

    class Meta:
        model = ProjectMember
        fields = "__all__"


class ProjectDetailViewSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    service = SerializerMethodField(read_only=True)
    creator = SerializerMethodField(read_only=True)
    modifier = SerializerMethodField(read_only=True)
    owner = SerializerMethodField(read_only=True)
    data_custodian = SerializerMethodField(read_only=True)
    site_custodian = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectDetail
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None

    def get_service(self, obj):
        service = obj.service
        if service:
            return {
                "pk": service.pk,
                "name": service.name,
            }
        return None

    def get_creator(self, obj):
        user = obj.creator
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_modifier(self, obj):
        user = obj.modifier
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }
        return None

    def get_owner(self, obj):
        user = obj.owner
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_data_custodian(self, obj):
        user = obj.data_custodian
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }
        return None

    def get_site_custodian(self, obj):
        user = obj.site_custodian
        if user:
            return {
                "pk": user.id,
                "username": user.username,
            }
        return None


class ProjectDetailSerializer(ModelSerializer):
    class Meta:
        model = ProjectDetail
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None

    def get_service(self, obj):
        service = obj.service
        if service:
            return {
                "pk": service.pk,
                "name": service.name,
            }
        return None

    def get_creator(self, obj):
        user = obj.creator
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_modifier(self, obj):
        user = obj.modifier
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }
        return None

    def get_owner(self, obj):
        user = obj.owner
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_data_custodian(self, obj):
        user = obj.data_custodian
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }
        return None

    def get_site_custodian(self, obj):
        user = obj.site_custodian
        if user:
            return {
                "pk": user.id,
                "username": user.username,
            }
        return None


class TinyProjectDetailSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    creator = SerializerMethodField(read_only=True)
    modifier = SerializerMethodField(read_only=True)
    owner = SerializerMethodField(read_only=True)
    data_custodian = SerializerMethodField(read_only=True)
    site_custodian = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectDetail
        fields = (
            "pk",
            "project",
            "creator",
            "modifier",
            "owner",
            "data_custodian",
            "site_custodian",
        )

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None

    def get_creator(self, obj):
        user = obj.creator
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_modifier(self, obj):
        user = obj.modifier
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_owner(self, obj):
        user = obj.owner
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_data_custodian(self, obj):
        user = obj.data_custodian
        if user:
            return {
                "pk": user.pk,
                "username": user.username,
            }
        return None

    def get_site_custodian(self, obj):
        user = obj.site_custodian
        if user:
            return {
                "id": user.id,
                "username": user.username,
            }
        return None


class StudentProjectDetailSerializer(ModelSerializer):
    # project = SerializerMethodField(read_only=True)

    class Meta:
        model = StudentProjectDetails
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None


class TinyStudentProjectDetailSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)

    class Meta:
        model = StudentProjectDetails
        fields = (
            "pk",
            "project",
            "level",
            "organisation",
        )

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None


class ExternalProjectDetailSerializer(ModelSerializer):
    class Meta:
        model = ExternalProjectDetails
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None


class TinyExternalProjectDetailSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)

    class Meta:
        model = ExternalProjectDetails
        fields = (
            "pk",
            "project",
            "collaboration_with",
            "budget",
            "description",
            "aims",
        )

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None


# endregion ==============================================
