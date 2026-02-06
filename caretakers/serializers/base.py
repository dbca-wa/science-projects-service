"""
Base caretaker serializers for list and detail views
"""
from rest_framework import serializers
from ..models import Caretaker
from users.serializers import BasicUserSerializer, MiniUserSerializer


class CaretakerSerializer(serializers.ModelSerializer):
    """Serializer for reading caretaker relationships"""
    id = serializers.IntegerField(read_only=True)
    user = MiniUserSerializer(read_only=True)
    caretaker = BasicUserSerializer(read_only=True)
    
    class Meta:
        model = Caretaker
        fields = [
            'id', 'user', 'caretaker', 'end_date', 
            'reason', 'notes', 'created_at', 'updated_at'
        ]
