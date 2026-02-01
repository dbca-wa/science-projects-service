"""
Update serializers for user and profile modifications
"""
from rest_framework import serializers

from users.models import User, UserProfile, UserWork


class UpdatePISerializer(serializers.ModelSerializer):
    """Update personal information serializer"""
    
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "display_first_name",
            "display_last_name",
            "email",
        )


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Update user profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = (
            "title",
            "expertise",
            "about",
        )


class UpdateMembershipSerializer(serializers.ModelSerializer):
    """Update user work/membership serializer"""
    
    class Meta:
        model = UserWork
        fields = (
            "title",
            "business_area",
            "affiliation",
            "branch",
        )


class UserWorkAffiliationUpdateSerializer(serializers.ModelSerializer):
    """Update user work affiliation serializer"""
    
    class Meta:
        model = UserWork
        fields = (
            "affiliation",
        )
