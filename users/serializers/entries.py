"""
Employment and education entry serializers
"""

from rest_framework import serializers

from users.models import EducationEntry, EmploymentEntry


class EmploymentEntrySerializer(serializers.ModelSerializer):
    """Employment entry serializer"""

    class Meta:
        model = EmploymentEntry
        fields = "__all__"


class EmploymentEntryCreationSerializer(serializers.ModelSerializer):
    """Employment entry creation serializer"""

    class Meta:
        model = EmploymentEntry
        fields = "__all__"


class EducationEntrySerializer(serializers.ModelSerializer):
    """Education entry serializer"""

    class Meta:
        model = EducationEntry
        fields = "__all__"


class EducationEntryCreationSerializer(serializers.ModelSerializer):
    """Education entry creation serializer"""

    class Meta:
        model = EducationEntry
        fields = "__all__"
