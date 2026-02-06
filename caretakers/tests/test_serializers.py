"""
Tests for caretaker serializers

Tests serialization and validation logic.
"""
import pytest
from django.utils import timezone
from datetime import timedelta

from caretakers.models import Caretaker
from caretakers.serializers.base import CaretakerSerializer
from caretakers.serializers.create import CaretakerCreateSerializer
from common.tests.factories import UserFactory


class TestCaretakerSerializer:
    """Tests for CaretakerSerializer (read-only)"""

    @pytest.mark.django_db
    def test_serialize_caretaker(self):
        """Test serializing a caretaker relationship"""
        # Arrange
        user = UserFactory(username='john')
        caretaker = UserFactory(username='jane')
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason='Going on leave',
            notes='Additional notes',
        )
        
        # Act
        serializer = CaretakerSerializer(relationship)
        data = serializer.data
        
        # Assert
        assert data['id'] == relationship.id
        assert data['user']['id'] == user.id
        assert data['user']['username'] == 'john'
        assert data['caretaker']['id'] == caretaker.id
        assert data['caretaker']['username'] == 'jane'
        assert data['reason'] == 'Going on leave'
        assert data['notes'] == 'Additional notes'
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.django_db
    def test_serialize_caretaker_with_end_date(self):
        """Test serializing caretaker with end_date"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        end_date = timezone.now() + timedelta(days=30)
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            end_date=end_date,
        )
        
        # Act
        serializer = CaretakerSerializer(relationship)
        data = serializer.data
        
        # Assert
        assert data['end_date'] is not None

    @pytest.mark.django_db
    def test_serialize_caretaker_without_optional_fields(self):
        """Test serializing caretaker without optional fields"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        # Act
        serializer = CaretakerSerializer(relationship)
        data = serializer.data
        
        # Assert
        assert data['end_date'] is None
        assert data['reason'] is None
        assert data['notes'] is None

    @pytest.mark.django_db
    def test_serialize_multiple_caretakers(self):
        """Test serializing multiple caretaker relationships"""
        # Arrange
        user = UserFactory()
        caretaker1 = UserFactory()
        caretaker2 = UserFactory()
        
        relationship1 = Caretaker.objects.create(
            user=user,
            caretaker=caretaker1,
            reason='Reason 1',
        )
        relationship2 = Caretaker.objects.create(
            user=user,
            caretaker=caretaker2,
            reason='Reason 2',
        )
        
        # Act
        serializer = CaretakerSerializer([relationship1, relationship2], many=True)
        data = serializer.data
        
        # Assert
        assert len(data) == 2
        assert data[0]['reason'] == 'Reason 1'
        assert data[1]['reason'] == 'Reason 2'

    @pytest.mark.django_db
    def test_serializer_fields(self):
        """Test serializer has correct fields"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        # Act
        serializer = CaretakerSerializer(relationship)
        
        # Assert
        expected_fields = {
            'id', 'user', 'caretaker', 'end_date',
            'reason', 'notes', 'created_at', 'updated_at'
        }
        assert set(serializer.data.keys()) == expected_fields

    @pytest.mark.django_db
    def test_id_field_read_only(self):
        """Test id field is read-only"""
        # Arrange
        serializer = CaretakerSerializer()
        
        # Assert
        assert serializer.fields['id'].read_only is True

    @pytest.mark.django_db
    def test_user_field_read_only(self):
        """Test user field is read-only"""
        # Arrange
        serializer = CaretakerSerializer()
        
        # Assert
        assert serializer.fields['user'].read_only is True

    @pytest.mark.django_db
    def test_caretaker_field_read_only(self):
        """Test caretaker field is read-only"""
        # Arrange
        serializer = CaretakerSerializer()
        
        # Assert
        assert serializer.fields['caretaker'].read_only is True


class TestCaretakerCreateSerializer:
    """Tests for CaretakerCreateSerializer"""

    @pytest.mark.django_db
    def test_create_caretaker_valid_data(self):
        """Test creating caretaker with valid data"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        data = {
            'user': user.pk,
            'caretaker': caretaker.pk,
            'reason': 'Going on leave',
            'notes': 'Additional notes',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        relationship = serializer.save()
        assert relationship.user == user
        assert relationship.caretaker == caretaker
        assert relationship.reason == 'Going on leave'
        assert relationship.notes == 'Additional notes'

    @pytest.mark.django_db
    def test_create_caretaker_with_end_date(self):
        """Test creating caretaker with end_date"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        end_date = timezone.now() + timedelta(days=30)
        data = {
            'user': user.pk,
            'caretaker': caretaker.pk,
            'end_date': end_date.isoformat(),
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        relationship = serializer.save()
        assert relationship.end_date is not None

    @pytest.mark.django_db
    def test_create_caretaker_minimal_data(self):
        """Test creating caretaker with minimal required data"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        data = {
            'user': user.pk,
            'caretaker': caretaker.pk,
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        relationship = serializer.save()
        assert relationship.user == user
        assert relationship.caretaker == caretaker
        assert relationship.reason is None
        assert relationship.notes is None

    @pytest.mark.django_db
    def test_validate_prevents_self_caretaking(self):
        """Test validation prevents self-caretaking"""
        # Arrange
        user = UserFactory()
        data = {
            'user': user.pk,
            'caretaker': user.pk,  # Same user
            'reason': 'Invalid',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'Cannot caretake for yourself' in str(serializer.errors)

    @pytest.mark.django_db
    def test_validate_prevents_duplicate_relationship(self):
        """Test validation prevents duplicate relationships"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        
        # Create existing relationship
        Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason='Existing relationship',
        )
        
        # Try to create duplicate
        data = {
            'user': user.pk,
            'caretaker': caretaker.pk,
            'reason': 'Duplicate',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        # Django's unique_together validator message
        assert 'unique set' in str(serializer.errors).lower()

    @pytest.mark.django_db
    def test_validate_allows_different_relationships(self):
        """Test validation allows different relationships"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        caretaker = UserFactory()
        
        # Create first relationship
        Caretaker.objects.create(
            user=user1,
            caretaker=caretaker,
        )
        
        # Create second relationship (different user)
        data = {
            'user': user2.pk,
            'caretaker': caretaker.pk,
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_validate_allows_reverse_relationship(self):
        """Test validation allows reverse relationships"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Create first relationship
        Caretaker.objects.create(
            user=user1,
            caretaker=user2,
        )
        
        # Create reverse relationship (should be allowed)
        data = {
            'user': user2.pk,
            'caretaker': user1.pk,
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_missing_required_user_field(self):
        """Test validation fails when user field is missing"""
        # Arrange
        caretaker = UserFactory()
        data = {
            'caretaker': caretaker.pk,
            'reason': 'Missing user',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'user' in serializer.errors

    @pytest.mark.django_db
    def test_missing_required_caretaker_field(self):
        """Test validation fails when caretaker field is missing"""
        # Arrange
        user = UserFactory()
        data = {
            'user': user.pk,
            'reason': 'Missing caretaker',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'caretaker' in serializer.errors

    @pytest.mark.django_db
    def test_invalid_user_id(self):
        """Test validation fails with invalid user ID"""
        # Arrange
        caretaker = UserFactory()
        data = {
            'user': 99999,  # Non-existent user
            'caretaker': caretaker.pk,
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'user' in serializer.errors

    @pytest.mark.django_db
    def test_invalid_caretaker_id(self):
        """Test validation fails with invalid caretaker ID"""
        # Arrange
        user = UserFactory()
        data = {
            'user': user.pk,
            'caretaker': 99999,  # Non-existent caretaker
        }
        
        # Act
        serializer = CaretakerCreateSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'caretaker' in serializer.errors

    @pytest.mark.django_db
    def test_serializer_fields(self):
        """Test serializer has correct fields"""
        # Arrange
        serializer = CaretakerCreateSerializer()
        
        # Assert
        expected_fields = {'user', 'caretaker', 'end_date', 'reason', 'notes'}
        assert set(serializer.fields.keys()) == expected_fields

    @pytest.mark.django_db
    def test_update_caretaker(self):
        """Test updating caretaker relationship"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason='Original reason',
        )
        
        data = {
            'reason': 'Updated reason',
            'notes': 'New notes',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(relationship, data=data, partial=True)
        
        # Assert
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.reason == 'Updated reason'
        assert updated.notes == 'New notes'

    @pytest.mark.django_db
    def test_partial_update_caretaker(self):
        """Test partial update of caretaker relationship"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason='Original reason',
        )
        
        data = {
            'notes': 'New notes only',
        }
        
        # Act
        serializer = CaretakerCreateSerializer(
            relationship,
            data=data,
            partial=True
        )
        
        # Assert
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.reason == 'Original reason'  # Unchanged
        assert updated.notes == 'New notes only'  # Updated
