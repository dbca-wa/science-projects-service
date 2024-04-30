from agencies.serializers import TinyBusinessAreaSerializer
from locations.models import Area
from medias.models import ProjectPhoto
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
    # ResearchFunction,
    StudentProjectDetails,
)
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers
from rest_framework.response import Response


# class TinyResearchFunctionSerializer(ModelSerializer):
#     class Meta:
#         model = ResearchFunction
#         fields = (
#             "pk",
#             "name",
#             "description",
#             "leader",
#             "association",
#             "is_active",
#         )


# class ResearchFunctionSerializer(ModelSerializer):
#     class Meta:
#         model = ResearchFunction
#         fields = "__all__"


class CreateProjectSerializer(ModelSerializer):
    # image = ProjectPhotoSerializer(read_only=True)
    image = ProjectPhotoSerializer(read_only=True)
    # business_area = TinyBusinessAreaSerializer()

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
    # image = ProjectPhotoSerializer(read_only=True)
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


class ProjectSerializer(ModelSerializer):
    # image = ProjectPhotoSerializer(read_only=True)
    image = ProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)

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


class TinyProjectSerializer(ModelSerializer):
    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    # level = serializers.SerializerMethodField()

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
            # "level",
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
        )


class ProjectAreaSerializer(serializers.ModelSerializer):
    # project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectArea
        fields = "__all__"
        # [
        #     "pk",
        #     "project",
        #     "areas",
        # ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        areas = instance.areas  # Access the list of area IDs directly

        # Fetch the related Area objects using the area IDs
        try:
            area_objects = Area.objects.filter(pk__in=areas)
        except Area.DoesNotExist:
            area_objects = []

        # Serialize the Area objects using the TinyAreaSerializer
        area_serializer = TinyAreaSerializer(area_objects, many=True)
        representation["areas"] = area_serializer.data

        return representation


class PkAndKindOnlyProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ["pk", "kind"]


class MiniUserSerializer(ModelSerializer):
    title = serializers.SerializerMethodField()
    affiliation = serializers.SerializerMethodField()

    def get_title(self, user):
        return user.profile.title

    def get_affiliation(self, user):
        return user.work.affiliation

    class Meta:
        model = User
        fields = [
            "pk",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "title",
            "affiliation",
        ]


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


class ProjectMemberSerializer(ModelSerializer):
    # user = TinyUserSerializer(read_only=True)
    # project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = "__all__"


class ProjectDetailViewSerializer(ModelSerializer):
    project = SerializerMethodField(read_only=True)
    # research_function = SerializerMethodField(read_only=True)
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

    # def get_research_function(self, obj):
    #     research_function = obj.research_function
    #     if research_function:
    #         return {
    #             "pk": research_function.pk,
    #             "name": research_function.name,
    #         }
    #     return None

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
    # project = SerializerMethodField(read_only=True)
    # research_function = SerializerMethodField(read_only=True)
    # creator = SerializerMethodField(read_only=True)
    # modifier = SerializerMethodField(read_only=True)
    # owner = SerializerMethodField(read_only=True)
    # data_custodian = SerializerMethodField(read_only=True)
    # site_custodian = SerializerMethodField(read_only=True)

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

    # def get_research_function(self, obj):
    #     research_function = obj.research_function
    #     if research_function:
    #         return {
    #             "pk": research_function.pk,
    #             "name": research_function.name,
    #         }
    #     return None

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
    # research_function = SerializerMethodField(read_only=True)
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
            # "research_function",
        )

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "pk": project.pk,
                "title": project.title,
            }
        return None

    # def get_research_function(self, obj):
    #     research_function = obj.research_function
    #     if research_function:
    #         return {
    #             "pk": research_function.pk,
    #             "name": research_function.name,
    #         }
    #     return None

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

    # def get_research_function(self, obj):
    #     research_function = obj.research_function
    #     if research_function:
    #         return {
    #             "pk": research_function.pk,
    #             "name": research_function.name,
    #         }
    #     return None


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
    # project = SerializerMethodField(read_only=True)
    # project = TinyProjectSerializer(read_only=True)

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

    # def get_project(self, obj):
    #     project = obj.project
    #     if project:
    #         return {
    #             "pk": project.pk,
    #             "title": project.title,
    #         }
    #     return None


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
