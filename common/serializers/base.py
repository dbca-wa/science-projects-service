"""
Base serializer classes for consistent data transformation
"""

from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base model serializer with common configuration

    Ensures consistent behavior:
    - Always uses 'id' field (not 'pk')
    - Provides common validation patterns
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize serializer and ensure 'id' is used instead of 'pk'
        """
        super().__init__(*args, **kwargs)

        # Ensure 'id' field is present if model has pk
        if hasattr(self.Meta, "model") and hasattr(self.Meta.model, "pk"):
            if "fields" in dir(self.Meta):
                fields = self.Meta.fields
                if isinstance(fields, (list, tuple)):
                    # Replace 'pk' with 'id' if present
                    if "pk" in fields:
                        fields = list(fields)
                        fields[fields.index("pk")] = "id"
                        self.Meta.fields = fields


class TimestampedSerializer(BaseModelSerializer):
    """
    Serializer for models with created_at and updated_at fields

    Automatically includes timestamp fields as read-only
    """

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
