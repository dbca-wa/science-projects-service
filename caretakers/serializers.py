# region IMPORTS
from rest_framework import serializers
from .models import Caretaker
from users.models import User
from users.serializers import BasicUserSerializer, MiniUserSerializer

# endregion


class CaretakerSerializer(serializers.ModelSerializer):
    """Serializer for reading caretaker relationships"""
    id = serializers.IntegerField(source='pk', read_only=True)
    user = MiniUserSerializer(read_only=True)
    caretaker = BasicUserSerializer(read_only=True)
    
    class Meta:
        model = Caretaker
        fields = [
            'id', 'user', 'caretaker', 'end_date', 
            'reason', 'notes', 'created_at', 'updated_at'
        ]


class CaretakerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating caretaker relationships"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    caretaker = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Caretaker
        fields = ['user', 'caretaker', 'end_date', 'reason', 'notes']
    
    def validate(self, data):
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
