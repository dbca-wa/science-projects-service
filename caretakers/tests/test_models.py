"""
Tests for caretaker models

Tests model creation, relationships, and methods.
"""

import pytest
from django.core.cache import cache
from django.db import IntegrityError

from caretakers.models import Caretaker
from common.tests.factories import UserFactory


class TestCaretakerModel:
    """Tests for Caretaker model"""

    @pytest.mark.django_db
    def test_create_caretaker(self):
        """Test creating a caretaker relationship"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()

        # Act
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason="Going on leave",
        )

        # Assert
        assert relationship.id is not None
        assert relationship.user == user
        assert relationship.caretaker == caretaker
        assert relationship.reason == "Going on leave"

    @pytest.mark.django_db
    def test_caretaker_str_representation(self):
        """Test string representation of caretaker"""
        # Arrange
        user = UserFactory(username="john")
        caretaker = UserFactory(username="jane")
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )

        # Act
        str_repr = str(relationship)

        # Assert
        assert "jane" in str_repr
        assert "john" in str_repr
        assert "caretaking for" in str_repr

    @pytest.mark.django_db
    def test_caretaker_unique_together_constraint(self):
        """Test unique_together constraint on user and caretaker"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason="First relationship",
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            Caretaker.objects.create(
                user=user,
                caretaker=caretaker,
                reason="Duplicate relationship",
            )

    @pytest.mark.django_db
    def test_caretaker_relationships(self):
        """Test ForeignKey relationships"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )

        # Act & Assert - Forward relationships
        assert relationship.user == user
        assert relationship.caretaker == caretaker

        # Act & Assert - Reverse relationships
        assert relationship in user.caretakers.all()
        assert relationship in caretaker.caretaking_for.all()

    @pytest.mark.django_db
    def test_caretaker_optional_fields(self):
        """Test optional fields can be null/blank"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()

        # Act
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            # No reason, notes, or end_date
        )

        # Assert
        assert relationship.reason is None
        assert relationship.notes is None
        assert relationship.end_date is None

    @pytest.mark.django_db
    def test_caretaker_with_end_date(self):
        """Test caretaker with end_date"""
        # Arrange
        from datetime import timedelta

        from django.utils import timezone

        user = UserFactory()
        caretaker = UserFactory()
        end_date = timezone.now() + timedelta(days=30)

        # Act
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            end_date=end_date,
        )

        # Assert
        assert relationship.end_date == end_date

    @pytest.mark.django_db
    def test_caretaker_with_notes(self):
        """Test caretaker with notes"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        notes = "Additional information about this caretaker relationship"

        # Act
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            notes=notes,
        )

        # Assert
        assert relationship.notes == notes

    @pytest.mark.django_db
    def test_caretaker_save_clears_cache(self):
        """Test save method clears cache for both users"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()

        # Set cache values
        cache.set(f"caretakers_{user.pk}", "test_value")
        cache.set(f"caretaking_{user.pk}", "test_value")
        cache.set(f"caretakers_{caretaker.pk}", "test_value")
        cache.set(f"caretaking_{caretaker.pk}", "test_value")

        # Act
        Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )

        # Assert - Cache should be cleared
        assert cache.get(f"caretakers_{user.pk}") is None
        assert cache.get(f"caretaking_{user.pk}") is None
        assert cache.get(f"caretakers_{caretaker.pk}") is None
        assert cache.get(f"caretaking_{caretaker.pk}") is None

    @pytest.mark.django_db
    def test_caretaker_delete_clears_cache(self):
        """Test delete method clears cache for both users"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )

        # Set cache values
        cache.set(f"caretakers_{user.pk}", "test_value")
        cache.set(f"caretaking_{user.pk}", "test_value")
        cache.set(f"caretakers_{caretaker.pk}", "test_value")
        cache.set(f"caretaking_{caretaker.pk}", "test_value")

        # Act
        relationship.delete()

        # Assert - Cache should be cleared
        assert cache.get(f"caretakers_{user.pk}") is None
        assert cache.get(f"caretaking_{user.pk}") is None
        assert cache.get(f"caretakers_{caretaker.pk}") is None
        assert cache.get(f"caretaking_{caretaker.pk}") is None

    @pytest.mark.django_db
    def test_caretaker_cascade_delete_on_user(self):
        """Test caretaker is deleted when user is deleted"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )

        # Act
        user.delete()

        # Assert
        assert not Caretaker.objects.filter(pk=relationship.pk).exists()

    @pytest.mark.django_db
    def test_caretaker_cascade_delete_on_caretaker(self):
        """Test caretaker is deleted when caretaker user is deleted"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )

        # Act
        caretaker.delete()

        # Assert
        assert not Caretaker.objects.filter(pk=relationship.pk).exists()

    @pytest.mark.django_db
    def test_caretaker_multiple_relationships(self):
        """Test user can have multiple caretakers"""
        # Arrange
        user = UserFactory()
        caretaker1 = UserFactory()
        caretaker2 = UserFactory()

        # Act
        relationship1 = Caretaker.objects.create(
            user=user,
            caretaker=caretaker1,
        )
        relationship2 = Caretaker.objects.create(
            user=user,
            caretaker=caretaker2,
        )

        # Assert
        assert user.caretakers.count() == 2
        assert relationship1 in user.caretakers.all()
        assert relationship2 in user.caretakers.all()

    @pytest.mark.django_db
    def test_caretaker_can_caretake_multiple_users(self):
        """Test caretaker can caretake for multiple users"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        caretaker = UserFactory()

        # Act
        relationship1 = Caretaker.objects.create(
            user=user1,
            caretaker=caretaker,
        )
        relationship2 = Caretaker.objects.create(
            user=user2,
            caretaker=caretaker,
        )

        # Assert
        assert caretaker.caretaking_for.count() == 2
        assert relationship1 in caretaker.caretaking_for.all()
        assert relationship2 in caretaker.caretaking_for.all()

    @pytest.mark.django_db
    def test_caretaker_meta_verbose_names(self):
        """Test model meta verbose names"""
        # Assert
        assert Caretaker._meta.verbose_name == "Caretaker"
        assert Caretaker._meta.verbose_name_plural == "Caretakers"

    @pytest.mark.django_db
    def test_caretaker_indexes(self):
        """Test model has correct indexes"""
        # Arrange
        indexes = [index.fields for index in Caretaker._meta.indexes]

        # Assert
        assert ["user"] in indexes
        assert ["caretaker"] in indexes
        assert ["end_date"] in indexes
