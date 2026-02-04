"""
Tests for common view classes
"""
import pytest
from unittest.mock import Mock, patch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework import status

from common.views.base import BaseAPIView


class TestBaseAPIView:
    """Tests for BaseAPIView"""

    def test_has_authentication_required_by_default(self):
        """Test BaseAPIView requires authentication by default"""
        # Arrange
        view = BaseAPIView()
        
        # Act & Assert
        assert IsAuthenticated in view.permission_classes

    def test_handle_exception_not_found(self):
        """Test handle_exception with NotFound exception"""
        # Arrange
        view = BaseAPIView()
        exc = NotFound("Resource not found")
        
        # Act
        response = view.handle_exception(exc)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data

    def test_handle_exception_permission_denied(self):
        """Test handle_exception with PermissionDenied exception"""
        # Arrange
        view = BaseAPIView()
        exc = PermissionDenied("Permission denied")
        
        # Act
        response = view.handle_exception(exc)
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'detail' in response.data

    def test_handle_exception_generic_exception(self):
        """Test handle_exception with generic exception"""
        # Arrange
        view = BaseAPIView()
        exc = Exception("Generic error")
        
        # Act
        response = view.handle_exception(exc)
        
        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_can_be_subclassed(self):
        """Test BaseAPIView can be subclassed"""
        # Arrange
        class MyView(BaseAPIView):
            def get(self, request):
                return Response({'message': 'success'})
        
        # Act
        view = MyView()
        
        # Assert
        assert isinstance(view, BaseAPIView)
        assert isinstance(view, APIView)
        assert hasattr(view, 'get')

    def test_subclass_inherits_permission_classes(self):
        """Test subclass inherits permission classes"""
        # Arrange
        class MyView(BaseAPIView):
            pass
        
        # Act
        view = MyView()
        
        # Assert
        assert IsAuthenticated in view.permission_classes

    def test_subclass_can_override_permission_classes(self):
        """Test subclass can override permission classes"""
        # Arrange
        from rest_framework.permissions import AllowAny
        
        class MyView(BaseAPIView):
            permission_classes = [AllowAny]
        
        # Act
        view = MyView()
        
        # Assert
        assert AllowAny in view.permission_classes
        assert IsAuthenticated not in view.permission_classes
