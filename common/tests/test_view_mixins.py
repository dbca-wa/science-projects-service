"""
Tests for common view mixins
"""
import pytest
from unittest.mock import Mock, patch
from django.conf import settings
from rest_framework import serializers
from rest_framework.response import Response

from common.views.mixins import SerializerValidationMixin, PaginationMixin


class TestSerializerValidationMixin:
    """Tests for SerializerValidationMixin"""

    def test_validate_and_save_success(self, db):
        """Test validate_and_save with valid data"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'username': 'testuser', 'email': 'test@example.com'}
        
        # Act
        obj, errors = mixin.validate_and_save(UserSerializer, data)
        
        # Assert
        assert obj is not None
        assert errors is None
        assert obj.username == 'testuser'
        assert obj.email == 'test@example.com'

    def test_validate_and_save_validation_error(self, db):
        """Test validate_and_save with invalid data"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'username': '', 'email': 'invalid'}  # Invalid data
        
        # Act
        obj, errors = mixin.validate_and_save(UserSerializer, data)
        
        # Assert
        assert obj is None
        assert errors is not None
        assert 'username' in errors or 'email' in errors

    def test_validate_and_save_with_instance(self, user, db):
        """Test validate_and_save updating existing instance"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'email': 'newemail@example.com'}
        
        # Act
        obj, errors = mixin.validate_and_save(
            UserSerializer,
            data,
            instance=user,
            partial=True
        )
        
        # Assert
        assert obj is not None
        assert errors is None
        assert obj.id == user.id
        assert obj.email == 'newemail@example.com'

    def test_validate_and_save_partial_update(self, user, db):
        """Test validate_and_save with partial update"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'username': 'newusername'}  # Only updating username
        
        # Act
        obj, errors = mixin.validate_and_save(
            UserSerializer,
            data,
            instance=user,
            partial=True
        )
        
        # Assert
        assert obj is not None
        assert errors is None
        assert obj.username == 'newusername'
        assert obj.email == user.email  # Email unchanged

    def test_validate_serializer_success(self, db):
        """Test validate_serializer with valid data"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'username': 'testuser', 'email': 'test@example.com'}
        
        # Act
        validated_data, errors = mixin.validate_serializer(UserSerializer, data)
        
        # Assert
        assert validated_data is not None
        assert errors is None
        assert validated_data['username'] == 'testuser'
        assert validated_data['email'] == 'test@example.com'

    def test_validate_serializer_validation_error(self, db):
        """Test validate_serializer with invalid data"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'username': '', 'email': 'invalid'}
        
        # Act
        validated_data, errors = mixin.validate_serializer(UserSerializer, data)
        
        # Assert
        assert validated_data is None
        assert errors is not None

    def test_validate_serializer_with_instance(self, user, db):
        """Test validate_serializer with existing instance"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['username', 'email']
        
        mixin = SerializerValidationMixin()
        data = {'email': 'newemail@example.com'}
        
        # Act
        validated_data, errors = mixin.validate_serializer(
            UserSerializer,
            data,
            instance=user,
            partial=True
        )
        
        # Assert
        assert validated_data is not None
        assert errors is None
        assert validated_data['email'] == 'newemail@example.com'


class TestPaginationMixin:
    """Tests for PaginationMixin"""

    def test_paginate_queryset_first_page(self, db):
        """Test paginating first page"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(25)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1'}
        
        mixin = PaginationMixin()
        
        # Act
        result = mixin.paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1
        assert result['total_results'] == 25
        assert result['total_pages'] == 2
        assert result['page_size'] == 20
        assert len(result['items']) == 20

    def test_paginate_queryset_custom_page_size(self, db):
        """Test paginating with custom page size"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(30)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1', 'page_size': '10'}
        
        mixin = PaginationMixin()
        
        # Act
        result = mixin.paginate_queryset(queryset, request)
        
        # Assert
        assert result['page_size'] == 10
        assert result['total_pages'] == 3
        assert len(result['items']) == 10

    def test_paginate_queryset_invalid_page(self, db):
        """Test paginating with invalid page number"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(10)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': 'invalid'}
        
        mixin = PaginationMixin()
        
        # Act
        result = mixin.paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1  # Defaults to 1

    def test_paginate_queryset_page_size_exceeds_max(self, db):
        """Test paginating with page size exceeding max"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(30)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1', 'page_size': '200'}
        
        mixin = PaginationMixin()
        
        # Act
        result = mixin.paginate_queryset(queryset, request)
        
        # Assert
        assert result['page_size'] == 100  # Capped at 100

    def test_paginated_response(self, db):
        """Test creating paginated response"""
        # Arrange
        from common.tests.factories import UserFactory
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = [UserFactory() for _ in range(25)]
        queryset = User.objects.all().order_by('id')
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['id', 'username', 'email']
        
        request = Mock()
        request.query_params = {'page': '1'}
        
        mixin = PaginationMixin()
        
        # Act
        response = mixin.paginated_response(
            queryset,
            UserSerializer,
            request
        )
        
        # Assert
        assert isinstance(response, Response)
        assert 'results' in response.data
        assert 'total_results' in response.data
        assert 'total_pages' in response.data
        assert 'current_page' in response.data
        assert 'page_size' in response.data
        assert len(response.data['results']) == 20
        assert response.data['total_results'] == 25
        assert response.data['total_pages'] == 2

    def test_paginated_response_with_serializer_kwargs(self, db):
        """Test paginated response with additional serializer kwargs"""
        # Arrange
        from common.tests.factories import UserFactory
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = [UserFactory() for _ in range(10)]
        queryset = User.objects.all().order_by('id')
        
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['id', 'username', 'email']
        
        request = Mock()
        request.query_params = {}
        
        mixin = PaginationMixin()
        
        # Act
        response = mixin.paginated_response(
            queryset,
            UserSerializer,
            request,
            context={'request': request}
        )
        
        # Assert
        assert isinstance(response, Response)
        assert len(response.data['results']) == 10

    def test_paginate_queryset_empty(self, db):
        """Test paginating empty queryset"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.none()
        
        request = Mock()
        request.query_params = {}
        
        mixin = PaginationMixin()
        
        # Act
        result = mixin.paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1
        assert result['total_results'] == 0
        assert result['total_pages'] == 0
        assert len(result['items']) == 0

    def test_paginate_queryset_negative_page(self, db):
        """Test paginating with negative page number"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(10)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '-1'}
        
        mixin = PaginationMixin()
        
        # Act
        result = mixin.paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1  # Negative converted to 1
