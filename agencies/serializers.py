# region IMPORTS ====================================================================================================
from rest_framework import serializers
from contacts.models import Address
from medias.models import BusinessAreaPhoto
from users.models import User
from .models import (
    Branch,
    BusinessArea,
    DepartmentalService,
    Agency,
    Affiliation,
    Division,
)

# endregion ====================================================================================================


class UserPkOnly(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("pk",)


# region Division Serializers ====================================================================================================


class UserInEmailListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()


class DirectorateEmailListSerializer(serializers.Serializer):
    """
    Serializer for the users in a directorate's email list
    """

    def to_representation(self, users):
        # Convert the users queryset to the desired format
        return [
            {
                "pk": user.pk,
                "email": user.email,
                "name": (
                    f"{user.display_first_name} {user.display_last_name}"
                    if hasattr(user, "display_first_name")
                    else user.get_full_name() or user.username
                ),
            }
            for user in users.all()
        ]


class TinyDivisionSerializer(serializers.ModelSerializer):

    directorate_email_list = DirectorateEmailListSerializer()

    class Meta:
        model = Division
        fields = (
            "pk",
            "name",
            "slug",
            "director",
            "approver",
            "directorate_email_list",
        )


class DivisionSerializer(serializers.ModelSerializer):
    directorate_email_list = DirectorateEmailListSerializer()

    class Meta:
        model = Division
        fields = "__all__"


# endregion  =================================================================================================


# region Departmental Service Serializers ====================================================================================================


class TinyDepartmentalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentalService
        fields = ("pk", "name", "director")


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
            "pk",
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
        agency_image = obj.image
        if agency_image and agency_image.file:
            return {
                "pk": agency_image.pk,
                "file": agency_image.file.url,
            }
        return None

    class Meta:
        model = Agency
        fields = (
            "pk",
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
            "pk",
            "name",
            "agency",
            "manager",
        ]


class MiniBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["pk", "name"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


# endregion  =================================================================================================


# region Business Area Serializers ====================================================================================================


class MiniBASerializer(serializers.ModelSerializer):
    leader = UserPkOnly()
    caretaker = UserPkOnly()

    class Meta:
        model = BusinessArea
        fields = ["pk", "name", "leader", "caretaker"]


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
        fields = ["pk", "file"]

    def to_representation(self, instance):
        return {
            "pk": instance.pk,
            "file": instance.file.url if instance.file else None,
        }


class TinyBusinessAreaSerializer(serializers.ModelSerializer):
    # Use the direct OneToOne relationship with medias app
    image = BusinessAreaImageSerializer(read_only=True)
    division = TinyDivisionSerializer(read_only=True)

    class Meta:
        model = BusinessArea
        fields = (
            "pk",
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
            "pk",
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
