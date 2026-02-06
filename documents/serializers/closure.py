"""
Project closure serializers
"""
from rest_framework import serializers

from ..models import ProjectClosure
from .base import TinyProjectDocumentSerializer


class TinyProjectClosureSerializer(serializers.ModelSerializer):
    """Minimal project closure serializer"""
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProjectClosure
        fields = [
            "id",
            "document",
            "reason",
            "intended_outcome",
            "knowledge_transfer",
            "data_location",
            "hardcopy_location",
        ]


class ProjectClosureSerializer(serializers.ModelSerializer):
    """Standard project closure serializer"""
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProjectClosure
        fields = "__all__"


class ProjectClosureCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating project closures"""
    
    class Meta:
        model = ProjectClosure
        fields = [
            "document",
            "reason",
            "intended_outcome",
            "knowledge_transfer",
            "data_location",
            "hardcopy_location",
        ]


class ProjectClosureUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating project closures"""
    
    class Meta:
        model = ProjectClosure
        fields = [
            "reason",
            "intended_outcome",
            "knowledge_transfer",
            "data_location",
            "hardcopy_location",
        ]
