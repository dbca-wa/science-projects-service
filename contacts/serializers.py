from rest_framework import serializers
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
    agency = TinyAgencySerializer()
    branch = TinyBranchSerializer()

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
