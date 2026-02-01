"""
Project member serializers
"""
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from agencies.serializers import AffiliationSerializer
from users.models import User
from users.serializers import TinyUserSerializer

from ..models import ProjectMember
from .base import TinyProjectSerializer, PkAndKindOnlyProjectSerializer


class ProjectMemberSerializer(ModelSerializer):
    """Full project member serializer"""
    
    def validate_role(self, value):
        if not value or value == "":
            raise serializers.ValidationError("Role is required.")
        return value

    class Meta:
        model = ProjectMember
        fields = "__all__"


class TinyProjectMemberSerializer(ModelSerializer):
    """Minimal project member serializer"""
    user = TinyUserSerializer(read_only=True)
    project = TinyProjectSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "id",
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


class MiniUserSerializer(ModelSerializer):
    """Mini user serializer for project members"""
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
            "id",
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
        caretakers = obj.get_caretakers()
        caretakers_data = [
            {
                "id": obj.caretaker.pk,
                "display_first_name": obj.caretaker.display_first_name,
                "display_last_name": obj.caretaker.display_last_name,
                "email": obj.caretaker.email,
            }
            for obj in caretakers
        ]
        return caretakers_data


class MiniProjectMemberSerializer(ModelSerializer):
    """Mini project member serializer with user details"""
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
