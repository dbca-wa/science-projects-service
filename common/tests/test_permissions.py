"""
Tests for common permission classes
"""
import pytest
from unittest.mock import Mock

from common.permissions.base import IsAdminUser, IsOwnerOrAdmin


class TestIsAdminUser:
    """Tests for IsAdminUser permission"""

    def test_has_permission_superuser(self, superuser, db):
        """Test superuser has permission"""
        # Arrange
        request = Mock(user=superuser)
        permission = IsAdminUser()
        
        # Act
        result = permission.has_permission(request, None)
        
        # Assert
        assert result is True

    def test_has_permission_regular_user(self, user, db):
        """Test regular user does not have permission"""
        # Arrange
        request = Mock(user=user)
        permission = IsAdminUser()
        
        # Act
        result = permission.has_permission(request, None)
        
        # Assert
        assert result is False

    def test_has_permission_no_user(self):
        """Test no user does not have permission"""
        # Arrange
        request = Mock(user=None)
        permission = IsAdminUser()
        
        # Act
        result = permission.has_permission(request, None)
        
        # Assert
        assert result is False

    def test_has_object_permission_superuser(self, superuser, db):
        """Test superuser has object permission"""
        # Arrange
        request = Mock(user=superuser)
        permission = IsAdminUser()
        obj = Mock()
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is True

    def test_has_object_permission_regular_user(self, user, db):
        """Test regular user does not have object permission"""
        # Arrange
        request = Mock(user=user)
        permission = IsAdminUser()
        obj = Mock()
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is False

    def test_has_object_permission_no_user(self):
        """Test no user does not have object permission"""
        # Arrange
        request = Mock(user=None)
        permission = IsAdminUser()
        obj = Mock()
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is False


class TestIsOwnerOrAdmin:
    """Tests for IsOwnerOrAdmin permission"""

    def test_has_object_permission_superuser(self, superuser, user, db):
        """Test superuser has permission regardless of ownership"""
        # Arrange
        request = Mock(user=superuser)
        permission = IsOwnerOrAdmin()
        obj = Mock(user=user)  # Object owned by different user
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is True

    def test_has_object_permission_owner_with_user_attribute(self, user, db):
        """Test owner has permission when object has user attribute"""
        # Arrange
        request = Mock(user=user)
        permission = IsOwnerOrAdmin()
        obj = Mock(user=user)
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is True

    def test_has_object_permission_owner_with_owner_attribute(self, user, db):
        """Test owner has permission when object has owner attribute"""
        # Arrange
        request = Mock(user=user)
        permission = IsOwnerOrAdmin()
        obj = Mock(spec=['owner'])
        obj.owner = user
        # Remove user attribute to test owner fallback
        if hasattr(obj, 'user'):
            delattr(obj, 'user')
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is True

    def test_has_object_permission_not_owner(self, user, db):
        """Test non-owner does not have permission"""
        # Arrange
        from common.tests.factories import UserFactory
        other_user = UserFactory()
        
        request = Mock(user=user)
        permission = IsOwnerOrAdmin()
        obj = Mock(user=other_user)
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is False

    def test_has_object_permission_no_user_or_owner_attribute(self, user, db):
        """Test permission denied when object has no user/owner attribute"""
        # Arrange
        request = Mock(user=user)
        permission = IsOwnerOrAdmin()
        obj = Mock(spec=[])  # Object with no user or owner attribute
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is False

    def test_has_object_permission_owner_attribute_takes_precedence(self, user, db):
        """Test user attribute is checked before owner attribute"""
        # Arrange
        from common.tests.factories import UserFactory
        other_user = UserFactory()
        
        request = Mock(user=user)
        permission = IsOwnerOrAdmin()
        obj = Mock(user=user, owner=other_user)  # user matches, owner doesn't
        
        # Act
        result = permission.has_object_permission(request, None, obj)
        
        # Assert
        assert result is True  # Should match on user attribute
