from rest_framework import serializers

from medias.models import BusinessAreaPhoto
from users.models import User

# from users.serializers import TinyUserSerializer
from .models import (
    Branch,
    BusinessArea,
    DepartmentalService,
    Agency,
    Affiliation,
    Division,
)

# from users.serializers import TinyUserSerializer


class AffiliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliation
        fields = (
            "pk",
            "created_at",
            "updated_at",
            "name",
        )


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


class UserPkOnly(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("pk",)


class MiniBASerializer(serializers.ModelSerializer):
    leader = UserPkOnly()

    class Meta:
        model = BusinessArea
        fields = ["pk", "name", "leader"]


class BusinessAreaSerializer(serializers.ModelSerializer):
    # pk = serializers.IntegerField(source="id")  # Map 'id' to 'pk'

    class Meta:
        model = BusinessArea
        fields = "__all__"


class TinyDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = (
            "pk",
            "name",
            "slug",
            "director",
            "approver",
        )


class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = "__all__"


class TinyBusinessAreaSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
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
            "image",
            "leader",
            "finance_admin",
            "data_custodian",
            "is_active",
        )
        ordering = ["name"]

    def get_image(self, obj):
        try:
            # Retrieve the related BusinessAreaPhoto object
            business_area_photo = BusinessAreaPhoto.objects.get(business_area=obj)

            # Get the image URL (choose old_file or file based on your requirement)
            pk = business_area_photo.pk
            # old_file = business_area_photo.old_file
            if business_area_photo.file:
                file = business_area_photo.file.url
            else:
                file = None
            # print({business_area_photo, file})
            return {
                "pk": pk,
                # "old_file": old_file,
                "file": file,
            }
        except BusinessAreaPhoto.DoesNotExist:
            # Return None if the image is not available
            return None


class TinyDepartmentalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentalService
        fields = ("pk", "name", "director")


class DepartmentalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentalService
        fields = "__all__"
