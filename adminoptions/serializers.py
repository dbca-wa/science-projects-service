from adminoptions.models import AdminOptions
from rest_framework import serializers

from users.serializers import MiniUserSerializer


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
