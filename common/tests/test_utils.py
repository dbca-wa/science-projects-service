"""
Tests for common utility functions
"""
import pytest
from unittest.mock import Mock
from datetime import date
from django.conf import settings
from rest_framework import serializers

from common.utils.pagination import (
    paginate_queryset,
    get_page_number,
    get_page_size,
)
from common.utils.validators import (
    validate_not_empty,
    validate_date_range,
    validate_positive_number,
    validate_file_size,
    validate_file_extension,
)
from common.utils.filters import (
    apply_search_filter,
    apply_date_range_filter,
    apply_status_filter,
    apply_boolean_filter,
)


class TestPaginationUtils:
    """Tests for pagination utilities"""

    def test_paginate_queryset_first_page(self, db):
        """Test pagination on first page"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(25)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1
        assert result['total_results'] == 25
        assert result['total_pages'] == 2  # 25 items / 20 per page = 2 pages
        assert result['page_size'] == 20
        assert len(result['items']) == 20

    def test_paginate_queryset_middle_page(self, db):
        """Test pagination on middle page"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(50)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '2'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 2
        assert result['total_results'] == 50
        assert result['total_pages'] == 3  # 50 items / 20 per page = 3 pages
        assert len(result['items']) == 20

    def test_paginate_queryset_last_page(self, db):
        """Test pagination on last page with partial results"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(25)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '2'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 2
        assert result['total_results'] == 25
        assert result['total_pages'] == 2
        assert len(result['items']) == 5  # Only 5 items on last page

    def test_paginate_queryset_empty(self, db):
        """Test pagination with empty queryset"""
        # Arrange
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.none()
        
        request = Mock()
        request.query_params = {}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1
        assert result['total_results'] == 0
        assert result['total_pages'] == 0
        assert len(result['items']) == 0

    def test_paginate_queryset_invalid_page_number(self, db):
        """Test pagination with invalid page number defaults to 1"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(10)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': 'invalid'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1

    def test_paginate_queryset_negative_page_number(self, db):
        """Test pagination with negative page number defaults to 1"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(10)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '-1'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['current_page'] == 1

    def test_paginate_queryset_custom_page_size(self, db):
        """Test pagination with custom page size"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(30)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1', 'page_size': '10'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['page_size'] == 10
        assert result['total_pages'] == 3  # 30 items / 10 per page = 3 pages
        assert len(result['items']) == 10

    def test_paginate_queryset_page_size_too_large(self, db):
        """Test pagination with page size exceeding max limit"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(30)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1', 'page_size': '200'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['page_size'] == 100  # Capped at max 100

    def test_paginate_queryset_invalid_page_size(self, db):
        """Test pagination with invalid page size uses default"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(30)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1', 'page_size': 'invalid'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['page_size'] == 20  # Default page size

    def test_get_page_number_valid(self):
        """Test extracting valid page number"""
        # Arrange
        request = Mock()
        request.query_params = {'page': '5'}
        
        # Act
        page = get_page_number(request)
        
        # Assert
        assert page == 5

    def test_get_page_number_default(self):
        """Test extracting page number with default"""
        # Arrange
        request = Mock()
        request.query_params = {}
        
        # Act
        page = get_page_number(request, default=10)
        
        # Assert
        assert page == 10

    def test_get_page_number_invalid(self):
        """Test extracting invalid page number returns default"""
        # Arrange
        request = Mock()
        request.query_params = {'page': 'invalid'}
        
        # Act
        page = get_page_number(request, default=1)
        
        # Assert
        assert page == 1

    def test_get_page_number_negative(self):
        """Test extracting negative page number returns 1"""
        # Arrange
        request = Mock()
        request.query_params = {'page': '-5'}
        
        # Act
        page = get_page_number(request)
        
        # Assert
        assert page == 1  # Negative pages are converted to 1

    def test_get_page_size_valid(self):
        """Test extracting valid page size"""
        # Arrange
        request = Mock()
        request.query_params = {'page_size': '50'}
        
        # Act
        page_size = get_page_size(request)
        
        # Assert
        assert page_size == 50

    def test_get_page_size_default(self):
        """Test extracting page size with default"""
        # Arrange
        request = Mock()
        request.query_params = {}
        
        # Act
        page_size = get_page_size(request, default=25)
        
        # Assert
        assert page_size == 25

    def test_get_page_size_exceeds_max(self):
        """Test extracting page size exceeding max limit"""
        # Arrange
        request = Mock()
        request.query_params = {'page_size': '200'}
        
        # Act
        page_size = get_page_size(request)
        
        # Assert
        assert page_size == 100  # Capped at max 100

    def test_get_page_size_below_min(self):
        """Test extracting page size below minimum"""
        # Arrange
        request = Mock()
        request.query_params = {'page_size': '0'}
        
        # Act
        page_size = get_page_size(request)
        
        # Assert
        assert page_size == 1  # Minimum is 1


class TestValidatorUtils:
    """Tests for validator utilities"""

    def test_validate_not_empty_valid(self):
        """Test validating non-empty string"""
        # Act
        result = validate_not_empty("test value", "Field")
        
        # Assert
        assert result == "test value"

    def test_validate_not_empty_with_whitespace(self):
        """Test validating string with leading/trailing whitespace"""
        # Act
        result = validate_not_empty("  test value  ", "Field")
        
        # Assert
        assert result == "test value"  # Whitespace stripped

    def test_validate_not_empty_empty_string(self):
        """Test validating empty string raises error"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Field cannot be empty"):
            validate_not_empty("", "Field")

    def test_validate_not_empty_whitespace_only(self):
        """Test validating whitespace-only string raises error"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Field cannot be empty"):
            validate_not_empty("   ", "Field")

    def test_validate_not_empty_none(self):
        """Test validating None raises error"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Field cannot be empty"):
            validate_not_empty(None, "Field")

    def test_validate_date_range_valid(self):
        """Test validating valid date range"""
        # Arrange
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        
        # Act & Assert - should not raise
        validate_date_range(start, end)

    def test_validate_date_range_same_date(self):
        """Test validating same start and end date"""
        # Arrange
        same_date = date(2024, 6, 15)
        
        # Act & Assert - should not raise
        validate_date_range(same_date, same_date)

    def test_validate_date_range_invalid(self):
        """Test validating invalid date range raises error"""
        # Arrange
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        
        # Act & Assert
        with pytest.raises(serializers.ValidationError):
            validate_date_range(start, end)

    def test_validate_date_range_none_start(self):
        """Test validating with None start date"""
        # Arrange
        end = date(2024, 12, 31)
        
        # Act & Assert - should not raise
        validate_date_range(None, end)

    def test_validate_date_range_none_end(self):
        """Test validating with None end date"""
        # Arrange
        start = date(2024, 1, 1)
        
        # Act & Assert - should not raise
        validate_date_range(start, None)

    def test_validate_positive_number_valid(self):
        """Test validating positive number"""
        # Act
        result = validate_positive_number(10, "Amount")
        
        # Assert
        assert result == 10

    def test_validate_positive_number_zero(self):
        """Test validating zero raises error"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Amount must be positive"):
            validate_positive_number(0, "Amount")

    def test_validate_positive_number_negative(self):
        """Test validating negative number raises error"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Amount must be positive"):
            validate_positive_number(-5, "Amount")

    def test_validate_positive_number_none(self):
        """Test validating None returns None"""
        # Act
        result = validate_positive_number(None, "Amount")
        
        # Assert
        assert result is None

    def test_validate_file_size_valid(self):
        """Test validating file within size limit"""
        # Arrange
        file = Mock()
        file.size = 5 * 1024 * 1024  # 5MB
        
        # Act & Assert - should not raise
        validate_file_size(file, max_size_mb=10)

    def test_validate_file_size_exceeds_limit(self):
        """Test validating file exceeding size limit raises error"""
        # Arrange
        file = Mock()
        file.size = 15 * 1024 * 1024  # 15MB
        
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="File size cannot exceed 10MB"):
            validate_file_size(file, max_size_mb=10)

    def test_validate_file_size_none(self):
        """Test validating None file"""
        # Act & Assert - should not raise
        validate_file_size(None, max_size_mb=10)

    def test_validate_file_extension_valid(self):
        """Test validating file with allowed extension"""
        # Arrange
        file = Mock()
        file.name = "document.pdf"
        
        # Act & Assert - should not raise
        validate_file_extension(file, ['.pdf', '.doc'])

    def test_validate_file_extension_invalid(self):
        """Test validating file with disallowed extension raises error"""
        # Arrange
        file = Mock()
        file.name = "document.exe"
        
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="File type not allowed"):
            validate_file_extension(file, ['.pdf', '.doc'])

    def test_validate_file_extension_case_insensitive(self):
        """Test validating file extension is case insensitive"""
        # Arrange
        file = Mock()
        file.name = "document.PDF"
        
        # Act & Assert - should not raise
        validate_file_extension(file, ['.pdf', '.doc'])

    def test_validate_file_extension_none(self):
        """Test validating None file"""
        # Act & Assert - should not raise
        validate_file_extension(None, ['.pdf', '.doc'])


class TestFilterUtils:
    """Tests for filter utilities"""

    def test_apply_search_filter_single_field(self, db):
        """Test applying search filter to single field"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(username='john_doe')
        user2 = UserFactory(username='jane_smith')
        user3 = UserFactory(username='bob_jones')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_search_filter(queryset, 'john', ['username'])
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_search_filter_multiple_fields(self, db):
        """Test applying search filter to multiple fields"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(username='john_doe', email='john@example.com')
        user2 = UserFactory(username='jane_smith', email='jane@example.com')
        user3 = UserFactory(username='bob_jones', email='bob@test.com')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_search_filter(queryset, 'example', ['username', 'email'])
        
        # Assert
        assert result.count() == 2
        assert user1 in result
        assert user2 in result

    def test_apply_search_filter_empty_search(self, db):
        """Test applying empty search filter returns all"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_search_filter(queryset, '', ['username'])
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_search_filter_none_search(self, db):
        """Test applying None search filter returns all"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_search_filter(queryset, None, ['username'])
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_search_filter_no_fields(self, db):
        """Test applying search filter with no fields returns all"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_search_filter(queryset, 'test', [])
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_date_range_filter_both_dates(self, db):
        """Test applying date range filter with both dates"""
        # Arrange
        from common.tests.factories import UserFactory
        from datetime import datetime, timedelta
        
        now = datetime.now()
        user1 = UserFactory()
        user1.date_joined = now - timedelta(days=10)
        user1.save()
        
        user2 = UserFactory()
        user2.date_joined = now - timedelta(days=5)
        user2.save()
        
        user3 = UserFactory()
        user3.date_joined = now - timedelta(days=1)
        user3.save()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        start = (now - timedelta(days=7)).date()
        end = (now - timedelta(days=2)).date()
        
        # Act
        result = apply_date_range_filter(queryset, 'date_joined', start, end)
        
        # Assert
        assert result.count() == 1
        assert user2 in result

    def test_apply_date_range_filter_start_only(self, db):
        """Test applying date range filter with start date only"""
        # Arrange
        from common.tests.factories import UserFactory
        from datetime import datetime, timedelta
        
        now = datetime.now()
        user1 = UserFactory()
        user1.date_joined = now - timedelta(days=10)
        user1.save()
        
        user2 = UserFactory()
        user2.date_joined = now - timedelta(days=5)
        user2.save()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        start = (now - timedelta(days=7)).date()
        
        # Act
        result = apply_date_range_filter(queryset, 'date_joined', start_date=start)
        
        # Assert
        assert result.count() == 1
        assert user2 in result

    def test_apply_date_range_filter_end_only(self, db):
        """Test applying date range filter with end date only"""
        # Arrange
        from common.tests.factories import UserFactory
        from datetime import datetime, timedelta
        
        now = datetime.now()
        user1 = UserFactory()
        user1.date_joined = now - timedelta(days=10)
        user1.save()
        
        user2 = UserFactory()
        user2.date_joined = now - timedelta(days=5)
        user2.save()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        end = (now - timedelta(days=7)).date()
        
        # Act
        result = apply_date_range_filter(queryset, 'date_joined', end_date=end)
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_date_range_filter_no_dates(self, db):
        """Test applying date range filter with no dates returns all"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_date_range_filter(queryset, 'date_joined')
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_status_filter_single_status(self, db):
        """Test applying status filter with single status"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        user3 = UserFactory(is_active=True)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_status_filter(queryset, True, 'is_active')
        
        # Assert
        assert result.count() == 2
        assert user1 in result
        assert user3 in result

    def test_apply_status_filter_multiple_statuses(self, db):
        """Test applying status filter with list of statuses"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True, is_staff=False)
        user2 = UserFactory(is_active=False, is_staff=True)
        user3 = UserFactory(is_active=True, is_staff=True)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_status_filter(queryset, [True, False], 'is_active')
        
        # Assert
        assert result.count() == 3  # All users match

    def test_apply_status_filter_none(self, db):
        """Test applying None status filter returns all"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_status_filter(queryset, None, 'is_active')
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_boolean_filter_true_string(self, db):
        """Test applying boolean filter with 'true' string"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, 'true', 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_boolean_filter_false_string(self, db):
        """Test applying boolean filter with 'false' string"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, 'false', 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user2 in result

    def test_apply_boolean_filter_one_string(self, db):
        """Test applying boolean filter with '1' string"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, '1', 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_boolean_filter_zero_string(self, db):
        """Test applying boolean filter with '0' string"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, '0', 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user2 in result

    def test_apply_boolean_filter_boolean_value(self, db):
        """Test applying boolean filter with boolean value"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, True, 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_boolean_filter_none(self, db):
        """Test applying None boolean filter returns all"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, None, 'is_active')
        
        # Assert
        assert result.count() == queryset.count()


    def test_paginate_queryset_page_size_below_min(self, db):
        """Test pagination with page size below minimum"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(30)]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all().order_by('id')
        
        request = Mock()
        request.query_params = {'page': '1', 'page_size': '0'}
        
        # Act
        result = paginate_queryset(queryset, request)
        
        # Assert
        assert result['page_size'] == 1  # Minimum is 1

    def test_get_page_size_none_default(self):
        """Test extracting page size with None default uses settings"""
        # Arrange
        request = Mock()
        request.query_params = {}
        
        # Act
        page_size = get_page_size(request, default=None)
        
        # Assert
        assert page_size == 20  # Default from settings

    def test_get_page_size_invalid(self):
        """Test extracting invalid page size returns default"""
        # Arrange
        request = Mock()
        request.query_params = {'page_size': 'invalid'}
        
        # Act
        page_size = get_page_size(request, default=25)
        
        # Assert
        assert page_size == 25


class TestValidatorUtilsAdditional:
    """Additional tests for validator utilities to achieve 100% coverage"""

    def test_validate_not_empty_custom_field_name(self):
        """Test validating empty string with custom field name"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Title cannot be empty"):
            validate_not_empty("", "Title")

    def test_validate_date_range_custom_field_names(self):
        """Test validating invalid date range with custom field names"""
        # Arrange
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        
        # Act & Assert
        with pytest.raises(serializers.ValidationError) as exc_info:
            validate_date_range(start, end, "start_date", "end_date")
        
        # Check error message contains custom field name
        assert "end_date" in str(exc_info.value) or "End Date" in str(exc_info.value)

    def test_validate_positive_number_custom_field_name(self):
        """Test validating negative number with custom field name"""
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="Price must be positive"):
            validate_positive_number(-10, "Price")

    def test_validate_file_size_custom_max_size(self):
        """Test validating file with custom max size"""
        # Arrange
        file = Mock()
        file.size = 3 * 1024 * 1024  # 3MB
        
        # Act & Assert
        with pytest.raises(serializers.ValidationError, match="File size cannot exceed 2MB"):
            validate_file_size(file, max_size_mb=2)

    def test_validate_file_extension_multiple_extensions(self):
        """Test validating file with multiple allowed extensions"""
        # Arrange
        file = Mock()
        file.name = "document.docx"
        
        # Act & Assert - should not raise
        validate_file_extension(file, ['.pdf', '.doc', '.docx', '.txt'])


class TestFilterUtilsAdditional:
    """Additional tests for filter utilities to achieve 100% coverage"""

    def test_apply_search_filter_case_insensitive(self, db):
        """Test search filter is case insensitive"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(username='JOHN_DOE')
        user2 = UserFactory(username='jane_smith')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_search_filter(queryset, 'john', ['username'])
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_date_range_filter_both_none(self, db):
        """Test date range filter with both dates None"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_date_range_filter(queryset, 'date_joined', None, None)
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_status_filter_empty_list(self, db):
        """Test status filter with empty list"""
        # Arrange
        from common.tests.factories import UserFactory
        users = [UserFactory() for _ in range(3)]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_status_filter(queryset, [], 'is_active')
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_status_filter_tuple(self, db):
        """Test status filter with tuple of statuses"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_status_filter(queryset, (True, False), 'is_active')
        
        # Assert
        assert result.count() == 2

    def test_apply_boolean_filter_yes_string(self, db):
        """Test boolean filter with 'yes' string"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, 'yes', 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_boolean_filter_uppercase_true(self, db):
        """Test boolean filter with uppercase 'TRUE' string"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, 'TRUE', 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user1 in result

    def test_apply_boolean_filter_false_boolean(self, db):
        """Test boolean filter with False boolean value"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=False)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        queryset = User.objects.all()
        
        # Act
        result = apply_boolean_filter(queryset, False, 'is_active')
        
        # Assert
        assert result.count() == 1
        assert user2 in result
