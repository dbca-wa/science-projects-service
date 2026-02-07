"""
Tests for common serializer classes
"""

from django.contrib.auth import get_user_model

from common.serializers.base import BaseModelSerializer, TimestampedSerializer

User = get_user_model()


class TestBaseModelSerializer:
    """Tests for BaseModelSerializer"""

    def test_init_replaces_pk_with_id_in_fields_list(self, db):
        """Test that pk is replaced with id in fields list"""

        # Arrange
        class TestSerializer(BaseModelSerializer):
            class Meta:
                model = User
                fields = ["pk", "username", "email"]

        # Act
        serializer = TestSerializer()

        # Assert
        assert "id" in serializer.Meta.fields
        assert "pk" not in serializer.Meta.fields

    def test_init_with_id_already_in_fields(self, db):
        """Test initialization when id is already in fields"""

        # Arrange
        class TestSerializer(BaseModelSerializer):
            class Meta:
                model = User
                fields = ["id", "username", "email"]

        # Act
        serializer = TestSerializer()

        # Assert
        assert "id" in serializer.Meta.fields
        assert serializer.Meta.fields.count("id") == 1  # Only one id

    def test_init_with_all_fields(self, db):
        """Test initialization with __all__ fields"""

        # Arrange
        class TestSerializer(BaseModelSerializer):
            class Meta:
                model = User
                fields = "__all__"

        # Act
        serializer = TestSerializer()

        # Assert
        # Should not raise error with __all__
        assert serializer.Meta.fields == "__all__"

    def test_init_with_tuple_fields(self, db):
        """Test initialization with tuple fields"""

        # Arrange
        class TestSerializer(BaseModelSerializer):
            class Meta:
                model = User
                fields = ("pk", "username", "email")

        # Act
        serializer = TestSerializer()

        # Assert
        assert "id" in serializer.Meta.fields
        assert "pk" not in serializer.Meta.fields

    def test_serialization(self, user, db):
        """Test serializing a model instance"""

        # Arrange
        class TestSerializer(BaseModelSerializer):
            class Meta:
                model = User
                fields = ["id", "username", "email"]

        # Act
        serializer = TestSerializer(user)

        # Assert
        assert serializer.data["id"] == user.id
        assert serializer.data["username"] == user.username
        assert serializer.data["email"] == user.email

    def test_deserialization(self, db):
        """Test deserializing data to create model"""

        # Arrange
        class TestSerializer(BaseModelSerializer):
            class Meta:
                model = User
                fields = ["username", "email", "password"]
                extra_kwargs = {"password": {"write_only": True}}

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "testpass123",
        }

        # Act
        serializer = TestSerializer(data=data)

        # Assert
        assert serializer.is_valid()


class TestTimestampedSerializer:
    """Tests for TimestampedSerializer"""

    def test_created_at_read_only(self, db):
        """Test created_at field is read-only"""

        # Arrange
        class TestSerializer(TimestampedSerializer):
            class Meta:
                model = User
                fields = ["id", "username", "created_at"]

        # Act
        serializer = TestSerializer()

        # Assert
        assert serializer.fields["created_at"].read_only is True

    def test_updated_at_read_only(self, db):
        """Test updated_at field is read-only"""

        # Arrange
        class TestSerializer(TimestampedSerializer):
            class Meta:
                model = User
                fields = ["id", "username", "updated_at"]

        # Act
        serializer = TestSerializer()

        # Assert
        assert serializer.fields["updated_at"].read_only is True

    def test_serialization_includes_timestamps(self, user, db):
        """Test serialization includes timestamp fields"""

        # Arrange
        class TestSerializer(TimestampedSerializer):
            class Meta:
                model = User
                fields = ["id", "username", "created_at", "updated_at"]

        # Act
        serializer = TestSerializer(user)

        # Assert
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data
        assert serializer.data["created_at"] is not None
        assert serializer.data["updated_at"] is not None

    def test_deserialization_ignores_timestamps(self, db):
        """Test deserialization ignores timestamp fields"""

        # Arrange
        class TestSerializer(TimestampedSerializer):
            class Meta:
                model = User
                fields = ["username", "email", "created_at", "updated_at"]

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "created_at": "2020-01-01T00:00:00Z",  # Should be ignored
            "updated_at": "2020-01-01T00:00:00Z",  # Should be ignored
        }

        # Act
        serializer = TestSerializer(data=data)

        # Assert
        assert serializer.is_valid()
        # Timestamps should not be in validated_data
        assert "created_at" not in serializer.validated_data
        assert "updated_at" not in serializer.validated_data

    def test_inherits_from_base_model_serializer(self, db):
        """Test TimestampedSerializer inherits from BaseModelSerializer"""

        # Arrange
        class TestSerializer(TimestampedSerializer):
            class Meta:
                model = User
                fields = ["pk", "username", "created_at"]

        # Act
        serializer = TestSerializer()

        # Assert
        # Should inherit pk → id replacement from BaseModelSerializer
        assert "id" in serializer.Meta.fields
        assert "pk" not in serializer.Meta.fields
