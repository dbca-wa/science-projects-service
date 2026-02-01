"""
Quote serializers
"""
from rest_framework import serializers
from quotes.models import Quote


class QuoteListSerializer(serializers.ModelSerializer):
    """Serializer for quote list"""
    
    class Meta:
        model = Quote
        fields = ['id', 'text', 'author']


class QuoteDetailSerializer(serializers.ModelSerializer):
    """Serializer for quote detail"""
    
    class Meta:
        model = Quote
        fields = '__all__'
