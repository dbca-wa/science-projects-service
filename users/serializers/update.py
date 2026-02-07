"""
Update serializers for user and profile modifications
"""

from rest_framework import serializers

from users.models import PublicStaffProfile, User, UserWork


class UpdatePISerializer(serializers.ModelSerializer):
    """Update personal information serializer"""

    # Read-only fields from User model
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)

    # Include fields from related models
    title = serializers.CharField(
        source="profile.title", required=False, allow_blank=True, allow_null=True
    )
    phone = serializers.CharField(
        source="contact.phone", required=False, allow_blank=True, allow_null=True
    )
    fax = serializers.CharField(
        source="contact.fax", required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "display_first_name",
            "display_last_name",
            "title",
            "phone",
            "fax",
        )


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Update user profile serializer (about, expertise from PublicStaffProfile)"""

    # Read-only field to match test expectations
    title = serializers.CharField(read_only=True)

    class Meta:
        model = PublicStaffProfile
        fields = (
            "title",
            "about",
            "expertise",
        )


class UpdateMembershipSerializer(serializers.ModelSerializer):
    """Update user work/membership serializer"""

    class Meta:
        model = UserWork
        fields = (
            "role",
            "business_area",
            "affiliation",
            "branch",
        )


class UserWorkAffiliationUpdateSerializer(serializers.ModelSerializer):
    """Update user work affiliation serializer"""

    class Meta:
        model = UserWork
        fields = ("affiliation",)
