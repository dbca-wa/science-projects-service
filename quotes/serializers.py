from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import Quote


class QuoteListSerializer(ModelSerializer):
    class Meta:
        model = Quote
        fields = [
            "pk",
            "text",
            "author",
            "created_at",
        ]


class QuoteDetailSerializer(ModelSerializer):
    class Meta:
        model = Quote
        fields = "__all__"
