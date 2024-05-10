from adminoptions.models import AdminOptions
from rest_framework import serializers


class AdminOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminOptions
        fields = (
            "pk",
            "created_at",
            "updated_at",
            "email_options",
        )
