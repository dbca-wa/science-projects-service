"""
Progress report serializers
"""
from rest_framework import serializers

from ..models import ProgressReport
from .base import TinyProjectDocumentSerializer


class TinyProgressReportSerializer(serializers.ModelSerializer):
    """Minimal progress report serializer"""
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProgressReport
        fields = [
            "id",
            "document",
            "year",
            "context",
            "aims",
            "progress",
            "implications",
            "future",
        ]


class ProgressReportSerializer(serializers.ModelSerializer):
    """Standard progress report serializer"""
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProgressReport
        fields = "__all__"


class ProgressReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating progress reports"""
    
    class Meta:
        model = ProgressReport
        fields = [
            "document",
            "year",
            "context",
            "aims",
            "progress",
            "implications",
            "future",
        ]


class ProgressReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating progress reports"""
    
    class Meta:
        model = ProgressReport
        fields = [
            "context",
            "aims",
            "progress",
            "implications",
            "future",
        ]
