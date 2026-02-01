"""
User profile serializers
"""
from rest_framework import serializers

from users.models import UserProfile


class TinyUserProfileSerializer(serializers.ModelSerializer):
    """Minimal user profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user",
            "title",
            "expertise",
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """Full user profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = "__all__"


class ProfilePageSerializer(serializers.ModelSerializer):
    """User profile serializer for profile page"""
    
    user = serializers.SerializerMethodField()
    work = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user",
            "work",
            "avatar",
            "title",
            "expertise",
            "about",
        )
    
    def get_user(self, obj):
        from .base import TinyUserSerializer
        return TinyUserSerializer(obj.user).data
    
    def get_work(self, obj):
        from .base import TinyUserWorkSerializer
        if hasattr(obj.user, 'work') and obj.user.work:
            return TinyUserWorkSerializer(obj.user.work).data
        return None
    
    def get_avatar(self, obj):
        try:
            if obj.user.avatar and obj.user.avatar.file:
                return obj.user.avatar.file.url
        except:
            pass
        return None
