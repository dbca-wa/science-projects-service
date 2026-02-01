"""
Project area serializers
"""
from rest_framework import serializers

from locations.models import Area
from locations.serializers import TinyAreaSerializer

from ..models import ProjectArea


class ProjectAreaSerializer(serializers.ModelSerializer):
    """Project area serializer with location details"""
    
    class Meta:
        model = ProjectArea
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        areas = instance.areas
        
        if areas:
            try:
                area_objects = Area.objects.filter(pk__in=areas)
                area_serializer = TinyAreaSerializer(area_objects, many=True)
                representation["areas"] = area_serializer.data
            except Area.DoesNotExist:
                representation["areas"] = []
        else:
            representation["areas"] = []
        
        return representation
