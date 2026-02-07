"""
Concept plan serializers
"""

from rest_framework import serializers

from ..models import ConceptPlan
from .base import TinyProjectDocumentSerializer


class TinyConceptPlanSerializer(serializers.ModelSerializer):
    """Minimal concept plan serializer"""

    document = TinyProjectDocumentSerializer()

    class Meta:
        model = ConceptPlan
        fields = [
            "id",
            "document",
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]


class ConceptPlanSerializer(serializers.ModelSerializer):
    """Standard concept plan serializer"""

    document = TinyProjectDocumentSerializer()

    class Meta:
        model = ConceptPlan
        fields = "__all__"


class ConceptPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating concept plans"""

    class Meta:
        model = ConceptPlan
        fields = [
            "document",
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]


class ConceptPlanUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating concept plans"""

    class Meta:
        model = ConceptPlan
        fields = [
            "background",
            "aims",
            "outcome",
            "collaborations",
            "strategic_context",
            "staff_time_allocation",
            "budget",
        ]
