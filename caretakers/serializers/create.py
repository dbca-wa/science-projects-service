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
        # Get user and caretaker from data or instance
        user = data.get('user', getattr(self.instance, 'user', None))
        caretaker = data.get('caretaker', getattr(self.instance, 'caretaker', None))
        
        # Prevent self-caretaking (only if both are provided)
        if user and caretaker and user == caretaker:
            raise serializers.ValidationError("Cannot caretake for yourself")
        
        return data
