"""
Student report serializers
"""
from rest_framework import serializers

from ..models import StudentReport
from .base import TinyProjectDocumentSerializer


class TinyStudentReportSerializer(serializers.ModelSerializer):
    """Minimal student report serializer"""
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = StudentReport
        fields = [
            "id",
            "document",
            "year",
            "progress_report",
        ]


class StudentReportSerializer(serializers.ModelSerializer):
    """Standard student report serializer"""
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = StudentReport
        fields = "__all__"


class StudentReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating student reports"""
    
    class Meta:
        model = StudentReport
        fields = [
            "document",
            "year",
            "progress_report",
        ]


class StudentReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating student reports"""
    
    class Meta:
        model = StudentReport
        fields = [
            "progress_report",
        ]
