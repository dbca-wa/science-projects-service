from rest_framework.serializers import ModelSerializer
from .models import Area


class TinyAreaSerializer(ModelSerializer):
    class Meta:
        model = Area
        fields = [
            "id",
            "name",
            "area_type",
        ]


class AreaSerializer(ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"
