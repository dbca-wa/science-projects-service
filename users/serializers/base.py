"""
Base user serializers
"""
from rest_framework import serializers

from agencies.serializers import (
    AffiliationSerializer,
    MiniBASerializer,
    TinyBusinessAreaSerializer,
)
from medias.models import UserAvatar
from medias.serializers import UserAvatarSerializer
from users.models import User, UserWork


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer"""
    
    class Meta:
        model = User
        exclude = ["password"]


class TinyUserSerializer(serializers.ModelSerializer):
    """Minimal user serializer for lists"""
    
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    affiliation = serializers.SerializerMethodField()
    business_area = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "display_first_name",
            "display_last_name",
            "name",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "image",
            "affiliation",
            "business_area",
        )
    
    def get_name(self, obj):
        return f"{obj.display_first_name} {obj.display_last_name}"
    
    def get_image(self, obj):
        try:
            return obj.avatar.file.url if obj.avatar and obj.avatar.file else None
        except UserAvatar.DoesNotExist:
            return None
    
    def get_affiliation(self, obj):
        if hasattr(obj, 'work') and obj.work:
            return AffiliationSerializer(obj.work.affiliation).data if obj.work.affiliation else None
        return None
    
    def get_business_area(self, obj):
        if hasattr(obj, 'work') and obj.work:
            return TinyBusinessAreaSerializer(obj.work.business_area).data if obj.work.business_area else None
        return None


class PrivateTinyUserSerializer(serializers.ModelSerializer):
    """Minimal user serializer without sensitive fields"""
    
    class Meta:
        model = User
        exclude = [
            "password",
            "is_superuser",
            "is_aec",
            "id",
            "is_staff",
            "is_active",
            "first_name",
            "last_name",
            "groups",
            "user_permissions",
        ]


class MiniUserSerializer(serializers.ModelSerializer):
    """User serializer with caretaker info"""
    
    caretakers = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "is_active",
            "is_staff",
            "caretakers",
        )
    
    def get_caretakers(self, obj):
        return [
            {
                "id": c.caretaker.id,
                "name": f"{c.caretaker.first_name} {c.caretaker.last_name}",
            }
            for c in obj.caretakers.all()
        ]


class BasicUserSerializer(serializers.ModelSerializer):
    """Basic user serializer with work info"""
    
    work = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "display_first_name",
            "display_last_name",
            "username",
            "email",
            "is_active",
            "is_staff",
            "work",
            "image",
        )
    
    def get_work(self, obj):
        if hasattr(obj, 'work') and obj.work:
            return {
                "id": obj.work.id,
                "title": obj.work.title,
                "business_area": MiniBASerializer(obj.work.business_area).data if obj.work.business_area else None,
            }
        return None
    
    def get_image(self, obj):
        try:
            return obj.avatar.file.url if obj.avatar and obj.avatar.file else None
        except UserAvatar.DoesNotExist:
            return None


class StaffProfileEmailListSerializer(serializers.ModelSerializer):
    """User serializer for email lists"""
    
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "image",
            "is_active",
            "is_staff",
        )
    
    def get_name(self, obj):
        return f"{obj.display_first_name} {obj.display_last_name}"
    
    def get_image(self, obj):
        try:
            return obj.avatar.file.url if obj.avatar and obj.avatar.file else None
        except UserAvatar.DoesNotExist:
            return None


class TinyUserWorkSerializer(serializers.ModelSerializer):
    """Minimal user work serializer"""
    
    business_area = TinyBusinessAreaSerializer(read_only=True)
    affiliation = AffiliationSerializer(read_only=True)
    
    class Meta:
        model = UserWork
        fields = (
            "id",
            "title",
            "business_area",
            "affiliation",
        )


class UserWorkSerializer(serializers.ModelSerializer):
    """Full user work serializer"""
    
    business_area = MiniBASerializer(read_only=True)
    affiliation = AffiliationSerializer(read_only=True)
    
    class Meta:
        model = UserWork
        fields = "__all__"
