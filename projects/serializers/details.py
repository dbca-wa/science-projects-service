"""
Project details serializers
"""

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from ..models import ExternalProjectDetails, ProjectDetail, StudentProjectDetails


class ProjectDetailSerializer(ModelSerializer):
    """Base project details serializer"""

    class Meta:
        model = ProjectDetail
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "id": project.pk,
                "title": project.title,
            }
        return None

    def get_service(self, obj):
        service = obj.service
        if service:
            return {
                "id": service.pk,
                "name": service.name,
            }
        return None

    def get_creator(self, obj):
        user = obj.creator
        if user:
            return {
                "id": user.pk,
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
                "id": user.pk,
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
                "id": user.id,
                "username": user.username,
            }
        return None


class ProjectDetailViewSerializer(ModelSerializer):
    """Project details view serializer with related data"""

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
                "id": project.pk,
                "title": project.title,
            }
        return None

    def get_service(self, obj):
        service = obj.service
        if service:
            return {
                "id": service.pk,
                "name": service.name,
            }
        return None

    def get_creator(self, obj):
        user = obj.creator
        if user:
            return {
                "id": user.pk,
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
                "id": user.pk,
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
                "id": user.id,
                "username": user.username,
            }
        return None


class TinyProjectDetailSerializer(ModelSerializer):
    """Minimal project details serializer"""

    project = SerializerMethodField(read_only=True)
    creator = SerializerMethodField(read_only=True)
    modifier = SerializerMethodField(read_only=True)
    owner = SerializerMethodField(read_only=True)
    data_custodian = SerializerMethodField(read_only=True)
    site_custodian = SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectDetail
        fields = (
            "id",
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
                "id": project.pk,
                "title": project.title,
            }
        return None

    def get_creator(self, obj):
        user = obj.creator
        if user:
            return {
                "id": user.pk,
                "username": user.username,
            }
        return None

    def get_modifier(self, obj):
        user = obj.modifier
        if user:
            return {
                "id": user.pk,
                "username": user.username,
            }
        return None

    def get_owner(self, obj):
        user = obj.owner
        if user:
            return {
                "id": user.pk,
                "username": user.username,
            }
        return None

    def get_data_custodian(self, obj):
        user = obj.data_custodian
        if user:
            return {
                "id": user.pk,
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
    """Student project details serializer"""

    class Meta:
        model = StudentProjectDetails
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "id": project.pk,
                "title": project.title,
            }
        return None


class TinyStudentProjectDetailSerializer(ModelSerializer):
    """Minimal student project details serializer"""

    project = SerializerMethodField(read_only=True)

    class Meta:
        model = StudentProjectDetails
        fields = (
            "id",
            "project",
            "level",
            "organisation",
        )

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "id": project.pk,
                "title": project.title,
            }
        return None


class ExternalProjectDetailSerializer(ModelSerializer):
    """External project details serializer"""

    class Meta:
        model = ExternalProjectDetails
        fields = "__all__"

    def get_project(self, obj):
        project = obj.project
        if project:
            return {
                "id": project.pk,
                "title": project.title,
            }
        return None


class TinyExternalProjectDetailSerializer(ModelSerializer):
    """Minimal external project details serializer"""

    project = SerializerMethodField(read_only=True)

    class Meta:
        model = ExternalProjectDetails
        fields = (
            "id",
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
                "id": project.pk,
                "title": project.title,
            }
        return None
