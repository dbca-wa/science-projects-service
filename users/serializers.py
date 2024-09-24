# region IMPORTS =====================================

# Project Imports -----------------------------
from math import e
from os import read
from agencies.models import Affiliation, Branch, BusinessArea
from agencies.serializers import (
    AffiliationSerializer,
    MiniBASerializer,
    MiniBranchSerializer,
    StaffProfileBranchSerializer,
    TinyAgencySerializer,
    TinyBranchSerializer,
    TinyBusinessAreaSerializer,
)
from medias.models import UserAvatar
from medias.serializers import StaffProfileAvatarSerializer, UserAvatarSerializer
from projects.models import ProjectMember
from .models import (
    EducationEntry,
    EmploymentEntry,
    KeywordTag,
    PublicStaffProfile,
    User,
    UserWork,
    UserProfile,
)

from rest_framework import serializers


# endregion

# region User Serializers =====================================


class StaffProfileEmailListSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "pk",
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
            # Access the avatar's file if it exists
            return obj.avatar.file.url if obj.avatar and obj.avatar.file else None
        except UserAvatar.DoesNotExist:
            # Return None if the avatar does not exist
            return None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]


class PrivateTinyUserSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = User
        fields = (
            "pk",
            "first_name",
            "last_name",
            "username",
            "email",
            "is_active",
            "is_superuser",
        )


class TinyUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="work.role")
    branch = TinyBranchSerializer(source="work.branch")
    business_area = TinyBusinessAreaSerializer(source="work.business_area")
    image = UserAvatarSerializer(source="profile.image")
    affiliation = AffiliationSerializer(source="work.affiliation")

    class Meta:
        model = User
        fields = (
            "pk",
            "display_first_name",
            "display_last_name",
            "first_name",
            "last_name",
            "username",
            "email",
            "is_active",
            "is_superuser",
            "is_aec",
            "is_staff",
            "image",
            "role",
            "branch",
            "business_area",
            "affiliation",
        )


class ManagerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()


# endregion

# region User Profile Serializers =====================================


class TinyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAvatar
        fields = ["file"]


class TinyUserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = (
            "pk",
            "user",
            "title",
            "middle_initials",
            "curriculum_vitae",
        )


class UserProfileSerializer(serializers.ModelSerializer):
    user = TinyUserSerializer(read_only=True)
    image = UserAvatarSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = "__all__"


class TinyUserWorkSerializer(serializers.ModelSerializer):
    user = TinyUserSerializer()
    agency = TinyAgencySerializer()
    branch = TinyBranchSerializer()
    business_area = TinyBusinessAreaSerializer()
    affiliation = AffiliationSerializer()

    class Meta:
        model = UserWork
        fields = (
            "pk",
            "user",
            "role",
            "agency",
            "branch",
            "business_area",
            "affiliation",
        )


class UserWorkSerializer(serializers.ModelSerializer):
    user = TinyUserSerializer()
    agency = TinyAgencySerializer()
    branch = TinyBranchSerializer()
    business_area = TinyBusinessAreaSerializer()
    affiliation = AffiliationSerializer()

    class Meta:
        model = UserWork
        fields = "__all__"


class UserWorkAffiliationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWork
        fields = [
            "affiliation",
        ]


class UpdatePISerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    display_first_name = serializers.CharField()
    display_last_name = serializers.CharField()
    title = serializers.CharField(
        source="profile.title",
        allow_blank=True,
        allow_null=True,
    )
    phone = serializers.CharField(
        source="contact.phone",
        allow_blank=True,
        allow_null=True,
    )
    fax = serializers.CharField(
        source="contact.fax",
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "display_first_name",
            "display_last_name",
            "email",
            "title",
            "fax",
            "phone",
        )

    def update(self, instance, validated_data):
        # Update the User fields
        instance.display_first_name = validated_data.get(
            "display_first_name", instance.display_first_name
        )
        instance.display_last_name = validated_data.get(
            "display_last_name", instance.display_last_name
        )

        # Save changes to the User model
        instance.save()

        profile_data = validated_data.pop("profile", None)
        contact_data = validated_data.pop("contact", None)

        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        if contact_data:
            contact = instance.contact
            for attr, value in contact_data.items():
                setattr(contact, attr, value)
            contact.save()

        return instance


class UpdateProfileSerializer(serializers.ModelSerializer):
    image = serializers.PrimaryKeyRelatedField(
        queryset=UserAvatar.objects.all(), source="staff_profile.image", required=False
    )
    about = serializers.CharField(
        source="staff_profile.about",
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    expertise = serializers.CharField(
        source="staff_profile.expertise",
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "image",
            "about",
            "expertise",
        )

    def update(self, instance, validated_data):
        staff_profile_data = validated_data.pop("staff_profile", None)

        if staff_profile_data:
            staff_profile = instance.staff_profile
            for attr, value in staff_profile_data.items():
                setattr(staff_profile, attr, value)
            staff_profile.save()

        return instance


class UpdateMembershipSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False
    )
    business_area = serializers.PrimaryKeyRelatedField(
        queryset=BusinessArea.objects.all(), required=False
    )
    affiliation = serializers.PrimaryKeyRelatedField(
        queryset=Affiliation.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = UserWork
        fields = (
            "affiliation",
            "branch",
            "business_area",
        )


class ProfilePageSerializer(serializers.ModelSerializer):
    # Profile
    image = UserAvatarSerializer(source="avatar")
    title = serializers.CharField(source="profile.title")
    about = serializers.CharField(source="staff_profile.about")
    expertise = serializers.CharField(source="staff_profile.expertise")
    # Work
    role = serializers.CharField(source="work.role")
    agency = TinyAgencySerializer(source="work.agency")
    branch = MiniBranchSerializer(source="work.branch")
    business_area = MiniBASerializer(source="work.business_area")
    affiliation = AffiliationSerializer(source="work.affiliation")
    # Contact
    phone = serializers.CharField(source="contact.phone")
    fax = serializers.CharField(source="contact.fax")
    # Staff Profile
    staff_profile_pk = serializers.PrimaryKeyRelatedField(
        source="staff_profile", read_only=True
    )
    public_email = serializers.EmailField(
        source="staff_profile.public_email",
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            "pk",
            "display_first_name",
            "display_last_name",
            "first_name",
            "last_name",
            "username",
            "email",
            "is_superuser",
            "is_aec",
            "is_staff",
            "is_active",
            "date_joined",
            "image",
            "role",
            "expertise",
            "about",
            "agency",
            "branch",
            "business_area",
            "title",
            "phone",
            "fax",
            "affiliation",
            "business_areas_led",
            "staff_profile_pk",
            "public_email",
        )


# endregion

# region Staff Profile Serializers =====================================


class TinyStaffProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="work.role")
    branch = StaffProfileBranchSerializer(source="work.branch")
    # business_area = StaffProfileBASerializer(source="work.business_area")
    it_asset_id = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()

    # New fields from the API response (if fetched)
    division = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "pk",
            "first_name",
            "last_name",
            "display_first_name",
            "display_last_name",
            "email",
            "is_active",
            "role",
            "branch",
            "employee_id",
            "it_asset_id",
            "division",
            "unit",
            "location",
            "position",
        )

    def get_employee_id(self, obj):
        return obj.staff_profile.employee_id

    def get_it_asset_id(self, obj):
        return obj.staff_profile.it_asset_id

    # New methods to fetch the dynamically added fields from the API data
    def get_division(self, obj):
        return getattr(obj, "division", None)

    def get_unit(self, obj):
        return getattr(obj, "unit", None)

    def get_location(self, obj):
        return getattr(obj, "location", None)

    def get_position(self, obj):
        return getattr(obj, "position", None)


class StaffProfileCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicStaffProfile
        fields = "__all__"


class UserStaffProfileSerializer(serializers.ModelSerializer):
    pk = serializers.PrimaryKeyRelatedField(read_only=True)
    display_first_name = serializers.CharField(read_only=True)
    display_last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    avatar = StaffProfileAvatarSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "pk",
            "display_first_name",
            "display_last_name",
            "email",
            "avatar",
        )


class KeywordTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeywordTag
        fields = ("pk", "name")

    def to_internal_value(self, data):
        if isinstance(data, dict):
            tag_name = data.get("name")
            tag_pk = data.get("pk")

            if tag_pk:
                try:
                    tag = KeywordTag.objects.get(pk=tag_pk)
                except KeywordTag.DoesNotExist:
                    raise serializers.ValidationError({"keyword_tags": "Invalid pk"})
            elif tag_name:
                tag, created = KeywordTag.objects.get_or_create(name=tag_name)
            else:
                raise serializers.ValidationError({"keyword_tags": "Invalid data"})

            return tag

        raise serializers.ValidationError({"keyword_tags": "Invalid data format"})


class StaffProfileHeroSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    user = UserStaffProfileSerializer()  # Nested serializer for user
    keyword_tags = KeywordTagSerializer(many=True)
    it_asset_data = serializers.SerializerMethodField()

    class Meta:
        model = PublicStaffProfile
        fields = (
            "pk",
            "user",
            "title",
            "keyword_tags",
            "name",
            "it_asset_data",
            "it_asset_id",
        )

    def get_name(self, obj):
        return f"{obj.user.display_first_name} {obj.user.display_last_name}"

    def get_it_asset_data(self, obj):
        it_asset_data = obj.get_it_asset_data()
        return it_asset_data


class StaffProfileOverviewSerializer(serializers.ModelSerializer):

    user = UserStaffProfileSerializer()  # Nested serializer for user

    class Meta:
        model = PublicStaffProfile
        fields = (
            "pk",
            "user",
            "about",
            "expertise",
        )


class EmploymentEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentEntry
        fields = (
            "pk",
            "public_profile",
            "position_title",
            "start_year",
            "end_year",
            "section",
            "employer",
        )


class EmploymentEntryCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentEntry
        fields = "__all__"


class EducationEntryCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationEntry
        fields = "__all__"


class EducationEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationEntry
        fields = (
            "pk",
            "public_profile",
            "qualification_kind",
            "qualification_field",
            "with_honours",
            "qualification_name",
            "start_year",
            "end_year",
            "institution",
            "location",
        )


class StaffProfileCVSerializer(serializers.ModelSerializer):

    employment = EmploymentEntrySerializer(many=True, source="employment_entries")
    education = EducationEntrySerializer(many=True, source="education_entries")

    class Meta:
        model = PublicStaffProfile
        fields = (
            "pk",
            "user",
            "employment",
            "education",
        )


class StaffProfileUserSerializer(serializers.ModelSerializer):
    # branch_name = serializers.SerializerMethodField()
    # business_area_name = serializers.SerializerMethodField()
    # title = serializers.SerializerMethodField()

    # def get_branch_name(self, obj):
    #     return obj.work.branch.name if obj.work and obj.work.branch else None

    # def get_business_area_name(self, obj):
    #     return (
    #         obj.work.business_area.name if obj.work and obj.work.business_area else None
    #     )

    def get_title(self, obj):
        return obj.profile.title if obj.profile else None

    class Meta:
        model = User
        fields = (
            "pk",
            "is_active",
            "display_first_name",
            "display_last_name",
            # "title",
            # "branch_name",
            # "business_area_name",
        )


class StaffProfileSerializer(serializers.ModelSerializer):
    user = StaffProfileUserSerializer(read_only=True)
    keyword_tags = KeywordTagSerializer(many=True)
    it_asset_data = serializers.SerializerMethodField()

    class Meta:
        model = PublicStaffProfile
        fields = (
            "pk",
            "it_asset_id",
            "employee_id",
            "is_hidden",
            "aucode",
            "user",
            # "dbca_position_title",
            "keyword_tags",
            "title",
            "about",
            "expertise",
            # "education",
            # "project_memberships",
            # "employment",
            # "publications",
            "it_asset_data",
            "public_email",
        )

    def get_it_asset_data(self, obj):
        # Get the it_asset_data from the context
        it_asset_data = self.context.get("it_asset_data")
        if it_asset_data and it_asset_data is not None:
            # Extract only the specified fields
            filtered_data = {
                "id": it_asset_data.get("id"),
                "employee_id": it_asset_data.get("employee_id"),
                # "email": it_asset_data.get("email"),
                "title": it_asset_data.get("title"),
                "division": it_asset_data.get("division"),
                "unit": it_asset_data.get("unit"),
                "location": it_asset_data.get("location", {}).get(
                    "name"
                ),  # Assuming location is a nested object
            }
            return filtered_data
        return None

    def update(self, instance, validated_data):
        # Handle the many-to-many field for keyword_tags
        if "keyword_tags" in validated_data:
            keyword_tags_data = validated_data.pop("keyword_tags", None)

            if keyword_tags_data is not None:
                instance.keyword_tags.clear()
                for tag in keyword_tags_data:
                    instance.keyword_tags.add(tag)

        return super().update(instance, validated_data)


# endregion

# region Other Serializers =====================================


class ProjectMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = ("project",)

    project = serializers.SerializerMethodField()

    def get_project(self, obj):
        return {
            "title": obj.project.title,
            "description": obj.project.description,
            "start_date": obj.project.start_date,
            "end_date": obj.project.start_date,
        }


class LocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)


# class ProjectEntrySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StaffProfileProjectEntry
#         fields = (
#             "public_profile",
#             "project_membership",
#             "flavour_text",
#         )

# endregion
