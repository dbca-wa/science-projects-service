# region IMPORTS ====================================================================================================
from rest_framework import serializers
from adminoptions.models import AdminOptions, AdminTask, Caretaker
from projects.models import Project
from users.models import User
from users.serializers import MiniUserSerializer

# endregion  =================================================================================================

# region Serializers ====================================================================================================


class AdminOptionsMaintainerSerializer(serializers.ModelSerializer):
    maintainer = MiniUserSerializer()

    class Meta:
        model = AdminOptions
        fields = ["maintainer"]


class AdminOptionsSerializer(serializers.ModelSerializer):
    maintainer = MiniUserSerializer()

    class Meta:
        model = AdminOptions
        fields = (
            "pk",
            "created_at",
            "updated_at",
            "email_options",
            "maintainer",
            "guide_admin",
            "guide_about",
            "guide_login",
            "guide_profile",
            "guide_user_creation",
            "guide_user_view",
            "guide_project_creation",
            "guide_project_view",
            "guide_project_team",
            "guide_documents",
            "guide_report",
        )


class IAdminTaskRequesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["pk", "display_first_name", "display_last_name"]


class AdminTaskRequestCreationSerializer(serializers.ModelSerializer):

    requester = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = AdminTask
        fields = "__all__"


class IAdminTaskProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["pk", "title"]


class SecondaryUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["pk", "display_first_name", "display_last_name"]


class AdminTaskSerializer(serializers.ModelSerializer):
    requester = IAdminTaskRequesterSerializer()
    primary_user = IAdminTaskRequesterSerializer()
    project = IAdminTaskProjectSerializer()
    secondary_users = serializers.SerializerMethodField()

    class Meta:
        model = AdminTask
        fields = "__all__"

    def get_secondary_users(self, obj):
        if obj.secondary_users:
            users = User.objects.filter(pk__in=obj.secondary_users)
            return SecondaryUserSerializer(users, many=True).data
        return []


class CaretakerSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()

    class Meta:
        model = Caretaker
        fields = "__all__"


# endregion  =================================================================================================
