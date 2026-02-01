"""
Serializers for creating caretaker relationships
"""
from rest_framework import serializers
from ..models import Caretaker
from users.models import User


class CaretakerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating caretaker relationships"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    caretaker = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Caretaker
        fields = ['user', 'caretaker', 'end_date', 'reason', 'notes']
    
    def validate(self, data):
        """Validate caretaker relationship"""
        # Prevent self-caretaking
        if data['user'] == data['caretaker']:
            raise serializers.ValidationError("Cannot caretake for yourself")
        
        # Check for existing relationship
        if Caretaker.objects.filter(
            user=data['user'],
            caretaker=data['caretaker']
        ).exists():
            raise serializers.ValidationError(
                "Caretaker relationship already exists"
            )
        
        return data
