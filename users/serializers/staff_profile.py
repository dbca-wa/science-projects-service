"""
Staff profile serializers
"""

from rest_framework import serializers

from medias.serializers import StaffProfileAvatarSerializer
from users.models import KeywordTag, PublicStaffProfile


class KeywordTagSerializer(serializers.ModelSerializer):
    """Keyword tag serializer"""

    class Meta:
        model = KeywordTag
        fields = "__all__"


class TinyStaffProfileSerializer(serializers.ModelSerializer):
    """Minimal staff profile serializer"""

    user = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    business_area = serializers.SerializerMethodField()

    class Meta:
        model = PublicStaffProfile
        fields = (
            "id",
            "user",
            "image",
            "business_area",
            "about",
            "expertise",
            "is_hidden",
        )

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "first_name": obj.user.display_first_name,
            "last_name": obj.user.display_last_name,
            "email": obj.user.email,
        }

    def get_image(self, obj):
        import logging

        logger = logging.getLogger(__name__)

        try:
            if obj.user.avatar and obj.user.avatar.file:
                return obj.user.avatar.file.url
        except Exception as e:
            logger.debug(f"Failed to get avatar for staff profile {obj.pk}: {e}")
        return None

    def get_business_area(self, obj):
        if hasattr(obj.user, "work") and obj.user.work and obj.user.work.business_area:
            return {
                "id": obj.user.work.business_area.id,
                "name": obj.user.work.business_area.name,
            }
        return None


class StaffProfileCreationSerializer(serializers.ModelSerializer):
    """Staff profile creation serializer"""

    class Meta:
        model = PublicStaffProfile
        fields = "__all__"


class StaffProfileHeroSerializer(serializers.ModelSerializer):
    """Staff profile hero section serializer"""

    user = serializers.SerializerMethodField()
    avatar = StaffProfileAvatarSerializer(source="user.avatar", read_only=True)
    work = serializers.SerializerMethodField()

    class Meta:
        model = PublicStaffProfile
        fields = (
            "id",
            "user",
            "avatar",
            "work",
            "about",
        )

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "first_name": obj.user.display_first_name,
            "last_name": obj.user.display_last_name,
            "email": (
                obj.public_email if obj.public_email_on and obj.public_email else None
            ),
        }

    def get_work(self, obj):
        if hasattr(obj.user, "work") and obj.user.work:
            work = obj.user.work
            return {
                "id": work.id,
                "role": (
                    obj.custom_title
                    if obj.custom_title_on and obj.custom_title
                    else work.role
                ),
                "business_area": (
                    {
                        "id": work.business_area.id,
                        "name": work.business_area.name,
                    }
                    if work.business_area
                    else None
                ),
            }
        return None


class StaffProfileOverviewSerializer(serializers.ModelSerializer):
    """Staff profile overview section serializer"""

    keywords = KeywordTagSerializer(source="keyword_tags", many=True, read_only=True)

    class Meta:
        model = PublicStaffProfile
        fields = (
            "id",
            "expertise",
            "keywords",
        )


class StaffProfileCVSerializer(serializers.ModelSerializer):
    """Staff profile CV section serializer"""

    employment_entries = serializers.SerializerMethodField()
    education_entries = serializers.SerializerMethodField()

    class Meta:
        model = PublicStaffProfile
        fields = (
            "id",
            "employment_entries",
            "education_entries",
        )

    def get_employment_entries(self, obj):
        from .entries import EmploymentEntrySerializer

        return EmploymentEntrySerializer(
            obj.employment_entries.all().order_by("-start_year"), many=True
        ).data

    def get_education_entries(self, obj):
        from .entries import EducationEntrySerializer

        return EducationEntrySerializer(
            obj.education_entries.all().order_by("-end_year"), many=True
        ).data


class StaffProfileSerializer(serializers.ModelSerializer):
    """Full staff profile serializer"""

    user = serializers.SerializerMethodField()
    avatar = StaffProfileAvatarSerializer(source="user.avatar", read_only=True)
    work = serializers.SerializerMethodField()
    keywords = KeywordTagSerializer(source="keyword_tags", many=True, read_only=True)
    employment_entries = serializers.SerializerMethodField()
    education_entries = serializers.SerializerMethodField()

    class Meta:
        model = PublicStaffProfile
        fields = (
            "id",
            "user",
            "avatar",
            "work",
            "about",
            "expertise",
            "keywords",
            "employment_entries",
            "education_entries",
            "is_hidden",
            "custom_title",
            "custom_title_on",
            "public_email",
            "public_email_on",
        )

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "first_name": obj.user.display_first_name,
            "last_name": obj.user.display_last_name,
            "email": (
                obj.public_email
                if obj.public_email_on and obj.public_email
                else obj.user.email
            ),
        }

    def get_work(self, obj):
        if hasattr(obj.user, "work") and obj.user.work:
            work = obj.user.work
            return {
                "id": work.id,
                "role": (
                    obj.custom_title
                    if obj.custom_title_on and obj.custom_title
                    else work.role
                ),
                "business_area": (
                    {
                        "id": work.business_area.id,
                        "name": work.business_area.name,
                    }
                    if work.business_area
                    else None
                ),
            }
        return None

    def get_employment_entries(self, obj):
        from .entries import EmploymentEntrySerializer

        return EmploymentEntrySerializer(
            obj.employment_entries.all().order_by("-start_year"), many=True
        ).data

    def get_education_entries(self, obj):
        from .entries import EducationEntrySerializer

        return EducationEntrySerializer(
            obj.education_entries.all().order_by("-end_year"), many=True
        ).data
