"""
Tests for caretaker serializers.

Tests the serializers in the caretakers app.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from users.models import User
from caretakers.models import Caretaker
from caretakers.serializers import CaretakerSerializer, CaretakerCreateSerializer


class CaretakerSerializerTest(TestCase):
    """Test CaretakerSerializer (for reading)"""

    def setUp(self):
        """Create test users and caretaker"""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
        )
        self.caretaker = Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test caretaker",
            notes="Test notes",
        )

    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        serializer = CaretakerSerializer(self.caretaker)
        data = serializer.data

        expected_fields = {
            "id",
            "user",
            "caretaker",
            "reason",
            "notes",
            "end_date",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_uses_id_not_pk(self):
        """Test serializer uses 'id' field not 'pk'"""
        serializer = CaretakerSerializer(self.caretaker)
        data = serializer.data

        self.assertIn("id", data)
        self.assertNotIn("pk", data)
        self.assertEqual(data["id"], self.caretaker.pk)

    def test_serializer_includes_nested_user_data(self):
        """Test serializer includes nested user objects"""
        serializer = CaretakerSerializer(self.caretaker)
        data = serializer.data

        # Check user field is nested
        self.assertIsInstance(data["user"], dict)
        self.assertEqual(data["user"]["id"], self.user1.pk)
        self.assertEqual(data["user"]["email"], "user1@example.com")

        # Check caretaker field is nested
        self.assertIsInstance(data["caretaker"], dict)
        self.assertEqual(data["caretaker"]["id"], self.user2.pk)
        self.assertEqual(data["caretaker"]["email"], "user2@example.com")

    def test_serializer_handles_null_end_date(self):
        """Test serializer handles null end_date"""
        serializer = CaretakerSerializer(self.caretaker)
        data = serializer.data

        self.assertIsNone(data["end_date"])

    def test_serializer_handles_end_date(self):
        """Test serializer handles end_date when present"""
        # Create unique users for this test to avoid duplicate constraint
        user3 = User.objects.create_user(
            username="user3",
            email="user3@example.com",
            first_name="User",
            last_name="Three",
        )
        user4 = User.objects.create_user(
            username="user4",
            email="user4@example.com",
            first_name="User",
            last_name="Four",
        )
        
        end_date = timezone.now() + timedelta(days=30)
        caretaker = Caretaker.objects.create(
            user=user3,
            caretaker=user4,
            reason="Temporary caretaker",
            end_date=end_date,
        )

        serializer = CaretakerSerializer(caretaker)
        data = serializer.data

        self.assertIsNotNone(data["end_date"])

    def test_serializer_many_true(self):
        """Test serializer works with many=True"""
        # Create another caretaker
        Caretaker.objects.create(
            user=self.user2,
            caretaker=self.user1,
            reason="Another caretaker",
        )

        caretakers = Caretaker.objects.all()
        serializer = CaretakerSerializer(caretakers, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertIsInstance(data, list)


class CaretakerCreateSerializerTest(TestCase):
    """Test CaretakerCreateSerializer (for creating)"""

    def setUp(self):
        """Create test users"""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
        )

    def test_create_serializer_valid_data(self):
        """Test create serializer with valid data"""
        data = {
            "user": self.user1.pk,
            "caretaker": self.user2.pk,
            "reason": "Going on leave",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        caretaker = serializer.save()
        self.assertEqual(caretaker.user, self.user1)
        self.assertEqual(caretaker.caretaker, self.user2)
        self.assertEqual(caretaker.reason, "Going on leave")

    def test_create_serializer_with_end_date(self):
        """Test create serializer with end_date"""
        end_date = timezone.now() + timedelta(days=30)
        data = {
            "user": self.user1.pk,
            "caretaker": self.user2.pk,
            "reason": "Temporary leave",
            "end_date": end_date,
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        caretaker = serializer.save()
        self.assertIsNotNone(caretaker.end_date)

    def test_create_serializer_with_notes(self):
        """Test create serializer with notes"""
        data = {
            "user": self.user1.pk,
            "caretaker": self.user2.pk,
            "reason": "Going on leave",
            "notes": "Additional notes",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        caretaker = serializer.save()
        self.assertEqual(caretaker.notes, "Additional notes")

    def test_create_serializer_prevents_self_caretaking(self):
        """Test create serializer prevents user from being their own caretaker"""
        data = {
            "user": self.user1.pk,
            "caretaker": self.user1.pk,
            "reason": "Self caretaking",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create_serializer_prevents_duplicate(self):
        """Test create serializer prevents duplicate caretaker relationships"""
        # Create first caretaker
        Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="First caretaker",
        )

        # Try to create duplicate
        data = {
            "user": self.user1.pk,
            "caretaker": self.user2.pk,
            "reason": "Duplicate caretaker",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create_serializer_requires_user(self):
        """Test create serializer requires user field"""
        data = {
            "caretaker": self.user2.pk,
            "reason": "Missing user",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)

    def test_create_serializer_requires_caretaker(self):
        """Test create serializer requires caretaker field"""
        data = {
            "user": self.user1.pk,
            "reason": "Missing caretaker",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("caretaker", serializer.errors)

    def test_create_serializer_reason_optional(self):
        """Test create serializer allows optional reason field"""
        data = {
            "user": self.user1.pk,
            "caretaker": self.user2.pk,
        }

        serializer = CaretakerCreateSerializer(data=data)
        # Reason is optional (blank=True, null=True in model)
        self.assertTrue(serializer.is_valid())
        
        caretaker = serializer.save()
        self.assertIsNone(caretaker.reason)

    def test_create_serializer_allows_multiple_caretakers_per_user(self):
        """Test create serializer allows multiple caretakers for same user"""
        user3 = User.objects.create_user(
            username="user3",
            email="user3@example.com",
        )

        # Create first caretaker
        Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="First caretaker",
        )

        # Create second caretaker for same user
        data = {
            "user": self.user1.pk,
            "caretaker": user3.pk,
            "reason": "Second caretaker",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        caretaker = serializer.save()
        self.assertEqual(Caretaker.objects.filter(user=self.user1).count(), 2)

    def test_create_serializer_allows_user_to_caretake_multiple(self):
        """Test create serializer allows user to caretake for multiple users"""
        user3 = User.objects.create_user(
            username="user3",
            email="user3@example.com",
        )

        # Create first caretaking relationship
        Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Caretaking for user1",
        )

        # Create second caretaking relationship with same caretaker
        data = {
            "user": user3.pk,
            "caretaker": self.user2.pk,
            "reason": "Caretaking for user3",
        }

        serializer = CaretakerCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        caretaker = serializer.save()
        self.assertEqual(Caretaker.objects.filter(caretaker=self.user2).count(), 2)
