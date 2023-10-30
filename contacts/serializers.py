from django.forms import ValidationError
from rest_framework import serializers
from agencies.models import Agency, Branch
from agencies.serializers import TinyBranchSerializer, TinyAgencySerializer
from .models import Address, AgencyContact, UserContact, BranchContact
from users.serializers import TinyUserSerializer


class TinyAddressSerializer(serializers.ModelSerializer):
    agency = TinyAgencySerializer()
    branch = TinyBranchSerializer()

    class Meta:
        model = Address
        fields = (
            "pk",
            "street",
            "city",
            "country",
            "agency",
            "branch",
            "pobox",
        )


class AddressSerializer(serializers.ModelSerializer):
    # agency = TinyAgencySerializer(required=True)
    # branch = TinyBranchSerializer(required=True)

    # agency = serializers.SerializerMethodField()
    # branch = serializers.SerializerMethodField()

    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), required=False  # Not required
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False  # Not required
    )

    def validate(self, data):
        agency = data.get("agency")
        branch = data.get("branch")

        if not agency and not branch:
            raise ValidationError(
                "Either 'agency' or 'branch' must have a value, but not both."
            )

        if agency and branch:
            raise ValidationError(
                "Only one of 'agency' or 'branch' can have a value, not both."
            )

        if branch and Address.objects.filter(branch=branch).exists():
            raise ValidationError("An address with the same branch already exists.")

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
