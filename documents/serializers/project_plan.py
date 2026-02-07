"""
Project plan serializers
"""

from rest_framework import serializers

from medias.serializers import AECPDFSerializer

from ..models import Endorsement, ProjectPlan
from .base import TinyProjectDocumentSerializer


class TinyProjectPlanSerializer(serializers.ModelSerializer):
    """Minimal project plan serializer"""

    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProjectPlan
        fields = [
            "id",
            "document",
            "background",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]


class ProjectPlanSerializer(serializers.ModelSerializer):
    """Standard project plan serializer"""

    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = ProjectPlan
        fields = "__all__"


class ProjectPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating project plans"""

    class Meta:
        model = ProjectPlan
        fields = [
            "document",
            "background",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]


class ProjectPlanUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating project plans"""

    class Meta:
        model = ProjectPlan
        fields = [
            "background",
            "aims",
            "outcome",
            "knowledge_transfer",
            "listed_references",
            "operating_budget",
            "operating_budget_external",
            "related_projects",
        ]


class TinyEndorsementSerializer(serializers.ModelSerializer):
    """Minimal endorsement serializer"""

    project_plan = TinyProjectPlanSerializer(read_only=True)
    aec_pdf = AECPDFSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = [
            "id",
            "project_plan",
            "ae_endorsement_required",
            "ae_endorsement_provided",
            "no_specimens",
            "data_management",
            "aec_pdf",
        ]


class MiniEndorsementSerializer(serializers.ModelSerializer):
    """Mini endorsement serializer with minimal fields"""

    project_plan = TinyProjectPlanSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = [
            "id",
            "project_plan",
        ]


class EndorsementSerializer(serializers.ModelSerializer):
    """Standard endorsement serializer"""

    project_plan = TinyProjectPlanSerializer(read_only=True)
    aec_pdf = AECPDFSerializer(read_only=True)

    class Meta:
        model = Endorsement
        fields = "__all__"


class EndorsementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating endorsements"""

    class Meta:
        model = Endorsement
        fields = [
            "project_plan",
            "ae_endorsement_required",
            "ae_endorsement_provided",
            "no_specimens",
            "data_management",
        ]


class EndorsementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating endorsements"""

    class Meta:
        model = Endorsement
        fields = [
            "ae_endorsement_required",
            "ae_endorsement_provided",
            "no_specimens",
            "data_management",
        ]
