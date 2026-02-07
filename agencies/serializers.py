# region IMPORTS ====================================================================================================
from rest_framework import serializers

from contacts.models import Address
from medias.models import BusinessAreaPhoto
from users.models import User

from .models import (
    Affiliation,
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Division,
)

# endregion ====================================================================================================


class UserPkOnly(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id",)


# region Division Serializers ====================================================================================================


class UserInEmailListSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk", read_only=True)
    name = serializers.CharField()
    email = serializers.EmailField()


class DirectorateEmailListSerializer(serializers.Serializer):
    """
    Serializer for the users in a directorate's email list
    """

    def to_representation(self, users):
        # Handle case where users might be a ManyRelatedManager or a prefetched queryset
        if hasattr(users, "all"):
            # It's a ManyRelatedManager, we need to call .all()
            user_list = users.all()
        else:
            # It's already a queryset/list from prefetch_related
            user_list = users

        return [
            {
                "id": user.pk,
                "email": user.email,
                "name": (
                    f"{user.display_first_name} {user.display_last_name}"
                    if hasattr(user, "display_first_name")
                    else user.get_full_name() or user.username
                ),
            }
            for user in user_list
        ]


class TinyDivisionSerializer(serializers.ModelSerializer):

    directorate_email_list = serializers.SerializerMethodField()

    class Meta:
        model = Division
        fields = (
            "id",
            "name",
            "slug",
            "director",
            "approver",
            "directorate_email_list",
        )

    def get_directorate_email_list(self, obj):
        return [
            {
                "id": user.pk,
                "email": user.email,
                "name": f"{user.display_first_name} {user.display_last_name}",
            }
            for user in obj.directorate_email_list.all()
        ]


class DivisionSerializer(serializers.ModelSerializer):
    directorate_email_list = DirectorateEmailListSerializer(read_only=True)

    class Meta:
        model = Division
        fields = "__all__"


# endregion  =================================================================================================


# region Departmental Service Serializers ====================================================================================================


class TinyDepartmentalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentalService
        fields = ("id", "name", "director")


class DepartmentalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentalService
        fields = "__all__"


# endregion  =================================================================================================


# region Affiliation Serializers ====================================================================================================


class AffiliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliation
        fields = (
            "id",
            "created_at",
            "updated_at",
            "name",
        )


# endregion  =================================================================================================


# region Agency Serializers ====================================================================================================


class TinyAgencySerializer(serializers.ModelSerializer):
    # Get the related image from medias.AgencyImage (as it has reverse accessor/related name of image)
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        import logging

        logger = logging.getLogger(__name__)

        try:
            agency_image = obj.image
            if agency_image and agency_image.file:
                return {
                    "id": agency_image.pk,
                    "file": agency_image.file.url,
                }
        except AttributeError as e:
            # Agency model doesn't have image relationship
            logger.debug(f"Agency {obj.pk} has no image relationship: {e}")
        return None

    class Meta:
        model = Agency
        fields = (
            "id",
            "name",
            "key_stakeholder",
            "is_active",
            "image",
        )


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = "__all__"


# endregion  =================================================================================================


# region Branch Serializers ====================================================================================================


class TinyBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = [
            "id",
            "name",
            "agency",
            "manager",
        ]


class MiniBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


# endregion  =================================================================================================


# region Business Area Serializers ====================================================================================================


class MiniBASerializer(serializers.ModelSerializer):
    leader = UserPkOnly()
    caretaker = UserPkOnly()
    image = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    division = serializers.SerializerMethodField()

    class Meta:
        model = BusinessArea
        fields = [
            "id",
            "name",
            "leader",
            "caretaker",
            "image",
            "project_count",
            "division",
        ]

    def get_image(self, obj):
        """Get the business area image file URL"""
        import logging

        logger = logging.getLogger(__name__)

        try:
            if obj.image and obj.image.file:
                return obj.image.file.url
        except Exception as e:
            logger.debug(f"Failed to get image for business area {obj.pk}: {e}")
        return None

    def get_project_count(self, obj):
        """Get the count of projects in this business area"""
        try:
            # Count all projects in this business area, not just active ones
            # since we want to show the total scope of the BA
            return obj.project_set.count()
        except Exception:
            return 0

    def get_division(self, obj):
        """Get division info"""
        if obj.division:
            return {
                "id": obj.division.id,
                "name": obj.division.name,
                "slug": obj.division.slug,
            }
        return None


class BusinessAreaSerializer(serializers.ModelSerializer):

    class Meta:
        model = BusinessArea
        fields = "__all__"


class BusinessAreaNameViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessArea
        fields = ["name"]
        ordering = ["name"]


class BusinessAreaImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessAreaPhoto
        fields = ["id", "file"]

    def to_representation(self, instance):
        return {
            "id": instance.pk,
            "file": instance.file.url if instance.file else None,
        }


class TinyBusinessAreaSerializer(serializers.ModelSerializer):
    # Use the direct OneToOne relationship with medias app
    image = BusinessAreaImageSerializer(read_only=True)
    division = TinyDivisionSerializer(read_only=True)

    class Meta:
        model = BusinessArea
        fields = (
            "id",
            "name",
            "slug",
            "focus",
            "division",
            "introduction",
            "image",  # OneToOne relation (prevent N+1)
            "leader",
            "caretaker",
            "finance_admin",
            "data_custodian",
            "is_active",
        )
        ordering = ["name"]


# endregion  =================================================================================================


# region Staff Profile Serializers ====================================================================================================


class StaffProfileAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = (
            "id",
            "street",
            "city",
            "state",
            "country",
            "zipcode",
            "pobox",
        )


class StaffProfileBranchSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    def get_address(self, obj):
        try:
            address = Address.objects.get(branch=obj)
            serializer = StaffProfileAddressSerializer(address)
            return serializer.data
        except Address.DoesNotExist:
            return None

    class Meta:
        model = Branch
        fields = ["name", "address"]


class StaffProfileBASerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessArea
        fields = "name"


# endregion  =================================================================================================
