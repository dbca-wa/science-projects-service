"""
Tests for caretaker permissions

Tests authorization logic for caretaker operations.
"""
import pytest
from unittest.mock import Mock

from caretakers.models import Caretaker
from caretakers.permissions.caretaker_permissions import (
    CanManageCaretaker,
    CanRespondToCaretakerRequest,
)
from common.tests.factories import UserFactory


class TestCanManageCaretaker:
    """Tests for CanManageCaretaker permission"""

    @pytest.mark.django_db
    def test_superuser_can_manage_any_caretaker(self):
        """Test superuser can manage any caretaker relationship"""
        # Arrange
        superuser = UserFactory(is_superuser=True)
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        request = Mock(user=superuser)
        permission = CanManageCaretaker()
        
        # Act
        result = permission.has_object_permission(request, None, relationship)
        
        # Assert
        assert result is True

    @pytest.mark.django_db
    def test_caretaker_can_manage_own_relationship(self):
        """Test caretaker can manage their own relationships"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        request = Mock(user=caretaker)
        permission = CanManageCaretaker()
        
        # Act
        result = permission.has_object_permission(request, None, relationship)
        
        # Assert
        assert result is True

    @pytest.mark.django_db
    def test_user_can_manage_own_caretaker_relationship(self):
        """Test user being caretaken can manage their relationships"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        request = Mock(user=user)
        permission = CanManageCaretaker()
        
        # Act
        result = permission.has_object_permission(request, None, relationship)
        
        # Assert
        assert result is True

    @pytest.mark.django_db
    def test_other_user_cannot_manage_caretaker(self):
        """Test other users cannot manage caretaker relationships"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()
        other_user = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        request = Mock(user=other_user)
        permission = CanManageCaretaker()
        
        # Act
        result = permission.has_object_permission(request, None, relationship)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_regular_user_cannot_manage_others_relationship(self):
        """Test regular user cannot manage other users' relationships"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user1,
            caretaker=caretaker,
        )
        
        request = Mock(user=user2)
        permission = CanManageCaretaker()
        
        # Act
        result = permission.has_object_permission(request, None, relationship)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_staff_user_without_superuser_cannot_manage(self):
        """Test staff user without superuser cannot manage relationships"""
        # Arrange
        staff_user = UserFactory(is_staff=True, is_superuser=False)
        user = UserFactory()
        caretaker = UserFactory()
        relationship = Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
        )
        
        request = Mock(user=staff_user)
        permission = CanManageCaretaker()
        
        # Act
        result = permission.has_object_permission(request, None, relationship)
        
        # Assert
        assert result is False


class TestCanRespondToCaretakerRequest:
    """Tests for CanRespondToCaretakerRequest permission"""

    @pytest.mark.django_db
    def test_superuser_can_respond_to_any_request(self):
        """Test superuser can respond to any caretaker request"""
        # Arrange
        superuser = UserFactory(is_superuser=True)
        
        # Mock AdminTask object
        admin_task = Mock()
        admin_task.secondary_users = [123, 456]
        
        request = Mock(user=superuser)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is True

    @pytest.mark.django_db
    def test_requested_caretaker_can_respond(self):
        """Test requested caretaker can respond to request"""
        # Arrange
        caretaker = UserFactory()
        
        # Mock AdminTask object with caretaker in secondary_users
        admin_task = Mock()
        admin_task.secondary_users = [caretaker.pk, 456]
        
        request = Mock(user=caretaker)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is True

    @pytest.mark.django_db
    def test_non_requested_user_cannot_respond(self):
        """Test non-requested user cannot respond to request"""
        # Arrange
        user = UserFactory()
        
        # Mock AdminTask object without user in secondary_users
        admin_task = Mock()
        admin_task.secondary_users = [123, 456]
        
        request = Mock(user=user)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_user_not_in_secondary_users_cannot_respond(self):
        """Test user not in secondary_users list cannot respond"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Mock AdminTask object with different users
        admin_task = Mock()
        admin_task.secondary_users = [user2.pk]
        
        request = Mock(user=user1)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_empty_secondary_users_denies_access(self):
        """Test empty secondary_users list denies access"""
        # Arrange
        user = UserFactory()
        
        # Mock AdminTask object with empty secondary_users
        admin_task = Mock()
        admin_task.secondary_users = []
        
        request = Mock(user=user)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_missing_secondary_users_attribute_denies_access(self):
        """Test missing secondary_users attribute denies access"""
        # Arrange
        user = UserFactory()
        
        # Mock AdminTask object without secondary_users attribute
        admin_task = Mock(spec=[])  # No attributes
        
        request = Mock(user=user)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_staff_user_without_superuser_cannot_respond(self):
        """Test staff user without superuser cannot respond"""
        # Arrange
        staff_user = UserFactory(is_staff=True, is_superuser=False)
        
        # Mock AdminTask object without staff user in secondary_users
        admin_task = Mock()
        admin_task.secondary_users = [123, 456]
        
        request = Mock(user=staff_user)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is False

    @pytest.mark.django_db
    def test_multiple_users_in_secondary_users(self):
        """Test permission works with multiple users in secondary_users"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        # Mock AdminTask object with multiple users
        admin_task = Mock()
        admin_task.secondary_users = [user1.pk, user2.pk, user3.pk]
        
        request = Mock(user=user2)
        permission = CanRespondToCaretakerRequest()
        
        # Act
        result = permission.has_object_permission(request, None, admin_task)
        
        # Assert
        assert result is True
