# region IMPORTS ====================================================================================================
from rest_framework import serializers
from agencies.models import Agency, Branch
from agencies.serializers import TinyBranchSerializer, TinyAgencySerializer
from .models import Address, AgencyContact, UserContact, BranchContact
from users.serializers import TinyUserSerializer

# endregion ====================================================================================================

# region Serializers ====================================================================================================


class TinyAddressSerializer(serializers.ModelSerializer):
    agency = TinyAgencySerializer()
    branch = TinyBranchSerializer()

    class Meta:
        model = Address
        fields = (
            "pk",
            "street",
            "city",
            "state",
            "country",
            "zipcode",
            "agency",
            "branch",
            "pobox",
        )


class AddressSerializer(serializers.ModelSerializer):
    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), required=False  # Not required
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False  # Not required
    )

    def validate(self, data):
        branch = data.get("branch")

        if branch:
            # Check if an address with the same branch already exists in the database during updates.
            if self.instance and self.instance.branch == branch:
                # Ignore the error when updating an existing address for the branch.
                pass
            elif Address.objects.filter(branch=branch).exists():
                raise serializers.ValidationError(
                    "An address with the same branch already exists."
                )

        return data

    def get_agency(self, obj):
        agency = obj.agency
        if agency:
            return {
                "pk": agency.pk,
                "name": agency.name,
                "key_stakeholder": agency.key_stakeholder,
                "is_active": agency.is_active,
                # You can add other fields from TinyAgencySerializer as needed
            }
        return None

    def get_branch(self, obj):
        branch = obj.branch
        if branch:
            return {
                "pk": branch.pk,
                "name": branch.name,
                "agency": branch.agency.pk,
                "manager": branch.manager,
                # You can add other fields from TinyBranchSerializer as needed
            }
        return None

    class Meta:
        model = Address
        fields = "__all__"


class TinyUserContactSerializer(serializers.ModelSerializer):
    user = TinyUserSerializer()

    class Meta:
        model = UserContact
        fields = (
            "pk",
            "user",
        )


class UserContactSerializer(serializers.ModelSerializer):
    user = TinyUserSerializer()

    class Meta:
        model = UserContact
        fields = "__all__"


class TinyAgencyContactSerializer(serializers.ModelSerializer):
    agency = TinyAgencySerializer()
    address = TinyAddressSerializer()

    class Meta:
        model = AgencyContact
        fields = (
            "pk",
            "agency",
            "email",
            "address",
        )


class AgencyContactSerializer(serializers.ModelSerializer):
    agency = TinyAgencySerializer()
    address = TinyAddressSerializer()

    class Meta:
        model = AgencyContact
        fields = "__all__"


class TinyBranchContactSerializer(serializers.ModelSerializer):
    branch = TinyBranchSerializer()
    address = TinyAddressSerializer()

    class Meta:
        model = BranchContact
        fields = [
            "pk",
            "branch",
            "email",
            "address",
        ]


class BranchContactSerializer(serializers.ModelSerializer):
    branch = TinyBranchSerializer()
    address = TinyAddressSerializer()

    class Meta:
        model = BranchContact
        fields = "__all__"


# endregion  =================================================================================================
