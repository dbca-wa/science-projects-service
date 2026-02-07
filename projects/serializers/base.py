"""
Base project serializers
"""

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from agencies.serializers import (
    BusinessAreaNameViewSerializer,
    TinyBusinessAreaSerializer,
)
from locations.models import Area
from locations.serializers import TinyAreaSerializer
from medias.serializers import ProjectPhotoSerializer, TinyProjectPhotoSerializer

from ..models import Project


class CreateProjectSerializer(ModelSerializer):
    """Serializer for creating projects"""

    image = ProjectPhotoSerializer(read_only=True)

    class Meta:
        model = Project
        fields = "__all__"


class ProjectSerializer(ModelSerializer):
    """Full project serializer with all related data"""

    image = ProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)
    deletion_request_id = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = "__all__"

    def get_deletion_request_id(self, instance):
        return instance.get_deletion_request_id()

    def get_areas(self, instance):
        area_ids = instance.area.areas
        if area_ids:
            areas = Area.objects.filter(id__in=area_ids)
            return TinyAreaSerializer(areas, many=True).data
        return []


class ProjectUpdateSerializer(ModelSerializer):
    """Serializer for updating projects"""

    image = ProjectPhotoSerializer(read_only=True)

    class Meta:
        model = Project
        fields = "__all__"


class TinyProjectSerializer(ModelSerializer):
    """Minimal project serializer"""

    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = TinyBusinessAreaSerializer(read_only=True)

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
        )


class ProblematicProjectSerializer(ModelSerializer):
    """Serializer for problematic projects view"""

    tag = serializers.SerializerMethodField()
    image = TinyProjectPhotoSerializer(read_only=True)
    business_area = BusinessAreaNameViewSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
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


class UserProfileProjectSerializer(ModelSerializer):
    """Serializer for projects on user profiles"""

    tag = serializers.SerializerMethodField()
    image = TinyProjectPhotoSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "title", "tag", "image"]

    def get_tag(self, obj):
        return obj.get_project_tag()


class PkAndKindOnlyProjectSerializer(ModelSerializer):
    """Minimal serializer with only ID and kind"""

    class Meta:
        model = Project
        fields = ["id", "kind"]
