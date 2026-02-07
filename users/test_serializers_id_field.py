"""
Unit tests for users app serializers to verify 'id' field standardization.

Tests verify that:
1. Serializers include 'id' field and not 'pk' field
2. 'id' value matches the model's pk value
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from users.serializers import (
    BasicUserSerializer,
    MiniUserSerializer,
    TinyUserSerializer,
)

User = get_user_model()


class UserSerializerIdFieldTestCase(TestCase):
    """Test that user serializers use 'id' instead of 'pk'"""

    def setUp(self):
        """Create test data"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            display_first_name="Test",
            display_last_name="User",
        )

    def test_mini_user_serializer_has_id_not_pk(self):
        """MiniUserSerializer should have 'id' field, not 'pk'"""
        serializer = MiniUserSerializer(self.user)
        data = serializer.data

        self.assertIn("id", data, "Serializer should have 'id' field")
        self.assertNotIn("pk", data, "Serializer should not have 'pk' field")
        self.assertEqual(data["id"], self.user.pk, "'id' value should match model's pk")

    def test_basic_user_serializer_has_id_not_pk(self):
        """BasicUserSerializer should have 'id' field, not 'pk'"""
        serializer = BasicUserSerializer(self.user)
        data = serializer.data

        self.assertIn("id", data, "Serializer should have 'id' field")
        self.assertNotIn("pk", data, "Serializer should not have 'pk' field")
        self.assertEqual(data["id"], self.user.pk, "'id' value should match model's pk")

    def test_tiny_user_serializer_has_id_not_pk(self):
        """TinyUserSerializer should have 'id' field, not 'pk'"""
        serializer = TinyUserSerializer(self.user)
        data = serializer.data

        self.assertIn("id", data, "Serializer should have 'id' field")
        self.assertNotIn("pk", data, "Serializer should not have 'pk' field")
        self.assertEqual(data["id"], self.user.pk, "'id' value should match model's pk")

    def test_multiple_users_have_correct_ids(self):
        """Test that multiple users have correct 'id' values"""
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        serializer1 = MiniUserSerializer(self.user)
        serializer2 = MiniUserSerializer(user2)

        self.assertEqual(serializer1.data["id"], self.user.pk)
        self.assertEqual(serializer2.data["id"], user2.pk)
        self.assertNotEqual(serializer1.data["id"], serializer2.data["id"])
