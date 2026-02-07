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
from users.models import User, UserWork


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer"""

    image = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()
    business_area = serializers.SerializerMethodField()
    affiliation = serializers.SerializerMethodField()
    business_areas_led = serializers.SerializerMethodField()
    caretakers = serializers.SerializerMethodField()
    caretaking_for = serializers.SerializerMethodField()
    about = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ["password"]

    def get_image(self, obj):
        try:
            return obj.avatar.file.url if obj.avatar and obj.avatar.file else None
        except UserAvatar.DoesNotExist:
            return None

    def get_role(self, obj):
        if hasattr(obj, "work") and obj.work:
            return obj.work.role
        return None

    def get_branch(self, obj):
        from agencies.serializers import TinyBranchSerializer

        if hasattr(obj, "work") and obj.work and obj.work.branch:
            return TinyBranchSerializer(obj.work.branch).data
        return None

    def get_business_area(self, obj):
        if hasattr(obj, "work") and obj.work and obj.work.business_area:
            return TinyBusinessAreaSerializer(obj.work.business_area).data
        return None

    def get_affiliation(self, obj):
        if hasattr(obj, "work") and obj.work and obj.work.affiliation:
            return AffiliationSerializer(obj.work.affiliation).data
        return None

    def get_business_areas_led(self, obj):
        if hasattr(obj, "business_areas_led"):
            return MiniBASerializer(obj.business_areas_led.all(), many=True).data
        return []

    def get_caretakers(self, obj):
        """Get users who are caretaking for this user"""
        return obj.get_caretakers_recursive(max_depth=5)

    def get_caretaking_for(self, obj):
        """Get users this user is caretaking for"""
        return obj.get_caretaking_recursive(max_depth=5)

    def get_about(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.about or ""
        return ""

    def get_expertise(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.expertise or ""
        return ""


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
        if hasattr(obj, "work") and obj.work:
            return (
                AffiliationSerializer(obj.work.affiliation).data
                if obj.work.affiliation
                else None
            )
        return None

    def get_business_area(self, obj):
        if hasattr(obj, "work") and obj.work:
            return (
                TinyBusinessAreaSerializer(obj.work.business_area).data
                if obj.work.business_area
                else None
            )
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
        if hasattr(obj, "work") and obj.work:
            return {
                "id": obj.work.id,
                "role": obj.work.role,
                "business_area": (
                    MiniBASerializer(obj.work.business_area).data
                    if obj.work.business_area
                    else None
                ),
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
            "role",
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


class UserMeSerializer(serializers.ModelSerializer):
    """User serializer for /me endpoint with caretaker relationships"""

    image = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()
    business_area = serializers.SerializerMethodField()
    affiliation = serializers.SerializerMethodField()
    business_areas_led = serializers.SerializerMethodField()
    caretakers = serializers.SerializerMethodField()
    caretaking_for = serializers.SerializerMethodField()
    about = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    fax = serializers.SerializerMethodField()
    staff_profile_id = serializers.SerializerMethodField()
    staff_profile_hidden = serializers.SerializerMethodField()
    public_email = serializers.SerializerMethodField()
    public_email_on = serializers.SerializerMethodField()
    custom_title = serializers.SerializerMethodField()
    custom_title_on = serializers.SerializerMethodField()
    agency = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "display_first_name",
            "display_last_name",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "is_active",
            "is_aec",
            "image",
            "role",
            "branch",
            "business_area",
            "business_areas_led",
            "affiliation",
            "caretakers",
            "caretaking_for",
            "date_joined",
            "about",
            "expertise",
            "title",
            "phone",
            "fax",
            "staff_profile_id",
            "staff_profile_hidden",
            "public_email",
            "public_email_on",
            "custom_title",
            "custom_title_on",
            "agency",
        )

    def get_image(self, obj):
        try:
            return obj.avatar.file.url if obj.avatar and obj.avatar.file else None
        except UserAvatar.DoesNotExist:
            return None

    def get_role(self, obj):
        if hasattr(obj, "work") and obj.work:
            return obj.work.role
        return None

    def get_branch(self, obj):
        from agencies.serializers import TinyBranchSerializer

        if hasattr(obj, "work") and obj.work and obj.work.branch:
            return TinyBranchSerializer(obj.work.branch).data
        return None

    def get_business_area(self, obj):
        if hasattr(obj, "work") and obj.work and obj.work.business_area:
            return TinyBusinessAreaSerializer(obj.work.business_area).data
        return None

    def get_affiliation(self, obj):
        if hasattr(obj, "work") and obj.work and obj.work.affiliation:
            return AffiliationSerializer(obj.work.affiliation).data
        return None

    def get_agency(self, obj):
        from agencies.serializers import TinyAgencySerializer

        if hasattr(obj, "work") and obj.work and obj.work.agency:
            return TinyAgencySerializer(obj.work.agency).data
        return None

    def get_business_areas_led(self, obj):
        if hasattr(obj, "business_areas_led"):
            return MiniBASerializer(obj.business_areas_led.all(), many=True).data
        return []

    def get_about(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.about or ""
        return ""

    def get_expertise(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.expertise or ""
        return ""

    def get_title(self, obj):
        if hasattr(obj, "profile") and obj.profile:
            return obj.profile.title or ""
        return ""

    def get_phone(self, obj):
        if hasattr(obj, "contact") and obj.contact:
            return obj.contact.phone or ""
        return ""

    def get_fax(self, obj):
        if hasattr(obj, "contact") and obj.contact:
            return obj.contact.fax or ""
        return ""

    def get_staff_profile_id(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.id
        return None

    def get_staff_profile_hidden(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.is_hidden
        return False

    def get_public_email(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.public_email or ""
        return ""

    def get_public_email_on(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.public_email_on
        return False

    def get_custom_title(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.custom_title or ""
        return ""

    def get_custom_title_on(self, obj):
        if hasattr(obj, "staff_profile") and obj.staff_profile:
            return obj.staff_profile.custom_title_on
        return False

    def get_caretakers(self, obj):
        """Get users who are caretaking for this user"""
        return obj.get_caretakers_recursive(max_depth=5)

    def get_caretaking_for(self, obj):
        """Get users this user is caretaking for"""
        return obj.get_caretaking_recursive(max_depth=5)
