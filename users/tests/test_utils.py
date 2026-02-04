"""
Tests for user utilities
"""
import pytest
from rest_framework.exceptions import ValidationError

from users.utils.filters import apply_user_filters, apply_profile_filters
from users.utils.helpers import (
    search_users,
    search_profiles,
    format_user_name,
    get_user_avatar_url,
    get_user_business_area,
)
from users.utils.validators import (
    validate_email_unique,
    validate_username_unique,
    validate_profile_data,
    validate_password_strength,
)
from users.models import User, PublicStaffProfile


class TestUserFilters:
    """Tests for user filtering utilities"""

    def test_apply_user_filters_is_active(self, user, db):
        # Arrange
        queryset = User.objects.all()
        filters = {'is_active': True}
        
        # Act
        result = apply_user_filters(queryset, filters)
        
        # Assert
        assert user in result
        assert result.filter(is_active=True).count() == result.count()

    def test_apply_user_filters_is_staff(self, staff_user, db):
        """Test filtering users by is_staff"""
        # Arrange
        queryset = User.objects.all()
        filters = {'is_staff': True}
        
        # Act
        result = apply_user_filters(queryset, filters)
        
        # Assert
        assert staff_user in result
        assert result.filter(is_staff=True).count() == result.count()

    def test_apply_user_filters_is_superuser(self, superuser, db):
        """Test filtering users by is_superuser"""
        # Arrange
        queryset = User.objects.all()
        filters = {'is_superuser': True}
        
        # Act
        result = apply_user_filters(queryset, filters)
        
        # Assert
        assert superuser in result
        assert result.filter(is_superuser=True).count() == result.count()

    def test_apply_user_filters_business_area(self, user, user_work, business_area, db):
        """Test filtering users by business area"""
        # Arrange
        queryset = User.objects.all()
        filters = {'business_area': business_area.id}
        
        # Act
        result = apply_user_filters(queryset, filters)
        
        # Assert
        assert user in result

    def test_apply_user_filters_multiple(self, user, db):
        """Test applying multiple filters"""
        # Arrange
        queryset = User.objects.all()
        filters = {
            'is_active': True,
            'is_staff': False,
        }
        
        # Act
        result = apply_user_filters(queryset, filters)
        
        # Assert
        assert user in result
        assert result.filter(is_active=True, is_staff=False).count() == result.count()

    def test_apply_user_filters_empty(self, user, db):
        """Test applying no filters"""
        # Arrange
        queryset = User.objects.all()
        filters = {}
        
        # Act
        result = apply_user_filters(queryset, filters)
        
        # Assert
        assert result.count() == queryset.count()

    def test_apply_profile_filters_business_area(self, staff_profile, user_work, business_area, db):
        """Test filtering profiles by business area"""
        # Arrange
        queryset = PublicStaffProfile.objects.all()
        filters = {'business_area': business_area.id}
        
        # Act
        result = apply_profile_filters(queryset, filters)
        
        # Assert
        assert staff_profile in result

    def test_apply_profile_filters_user(self, staff_profile, db):
        """Test filtering profiles by user"""
        # Arrange
        queryset = PublicStaffProfile.objects.all()
        filters = {'user': staff_profile.user.id}
        
        # Act
        result = apply_profile_filters(queryset, filters)
        
        # Assert
        assert staff_profile in result
        assert result.count() == 1


class TestUserHelpers:
    """Tests for user helper utilities"""

    def test_search_users_by_username(self, user, db):
        """Test searching users by username"""
        # Arrange
        queryset = User.objects.all()
        search_term = user.username[:5]
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert user in result

    def test_search_users_by_email(self, user, db):
        """Test searching users by email"""
        # Arrange
        queryset = User.objects.all()
        search_term = user.email[:5]
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert user in result

    def test_search_users_by_first_name(self, user, db):
        """Test searching users by first name"""
        # Arrange
        queryset = User.objects.all()
        search_term = user.first_name[:3]
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert user in result

    def test_search_users_by_last_name(self, user, db):
        """Test searching users by last name"""
        # Arrange
        queryset = User.objects.all()
        search_term = user.last_name[:3]
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert user in result

    def test_search_users_by_full_name(self, user, db):
        """Test searching users by full name"""
        # Arrange
        queryset = User.objects.all()
        search_term = f"{user.first_name} {user.last_name}"
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert user in result

    def test_search_users_empty_term(self, user, db):
        """Test searching with empty term"""
        # Arrange
        queryset = User.objects.all()
        search_term = ""
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert result.count() == queryset.count()

    def test_search_users_short_term(self, user, db):
        """Test searching with term less than 2 characters"""
        # Arrange
        queryset = User.objects.all()
        search_term = "a"
        
        # Act
        result = search_users(queryset, search_term)
        
        # Assert
        assert result.count() == queryset.count()

    def test_search_profiles_by_user_name(self, staff_profile, db):
        """Test searching profiles by user name"""
        # Arrange
        queryset = PublicStaffProfile.objects.all()
        search_term = staff_profile.user.first_name[:3]
        
        # Act
        result = search_profiles(queryset, search_term)
        
        # Assert
        assert staff_profile in result

    def test_search_profiles_by_email(self, staff_profile, db):
        """Test searching profiles by email"""
        # Arrange
        queryset = PublicStaffProfile.objects.all()
        search_term = staff_profile.user.email[:5]
        
        # Act
        result = search_profiles(queryset, search_term)
        
        # Assert
        assert staff_profile in result

    def test_search_profiles_by_about(self, staff_profile, db):
        """Test searching profiles by about text"""
        # Arrange
        staff_profile.about = "Expert in Python development"
        staff_profile.save()
        queryset = PublicStaffProfile.objects.all()
        search_term = "Python"
        
        # Act
        result = search_profiles(queryset, search_term)
        
        # Assert
        assert staff_profile in result

    def test_search_profiles_by_expertise(self, staff_profile, db):
        """Test searching profiles by expertise"""
        # Arrange
        staff_profile.expertise = "Django, REST APIs"
        staff_profile.save()
        queryset = PublicStaffProfile.objects.all()
        search_term = "Django"
        
        # Act
        result = search_profiles(queryset, search_term)
        
        # Assert
        assert staff_profile in result

    def test_search_profiles_empty_term(self, staff_profile, db):
        """Test searching profiles with empty term"""
        # Arrange
        queryset = PublicStaffProfile.objects.all()
        search_term = ""
        
        # Act
        result = search_profiles(queryset, search_term)
        
        # Assert
        assert result.count() == queryset.count()

    def test_format_user_name(self, user, db):
        """Test formatting user name"""
        # Act
        result = format_user_name(user)
        
        # Assert
        assert result == f"{user.display_first_name} {user.display_last_name}"

    def test_get_user_avatar_url_no_avatar(self, user, db):
        """Test getting avatar URL when user has no avatar"""
        # Act
        result = get_user_avatar_url(user)
        
        # Assert
        assert result is None

    def test_get_user_business_area_with_work(self, user, user_work, business_area, db):
        """Test getting user business area when work exists"""
        # Act
        result = get_user_business_area(user)
        
        # Assert
        assert result == business_area

    def test_get_user_business_area_no_work(self, user_factory, db):
        """Test getting user business area when no work"""
        # Arrange
        user = user_factory()
        
        # Act
        result = get_user_business_area(user)
        
        # Assert
        assert result is None


class TestUserValidators:
    """Tests for user validation utilities"""

    def test_validate_email_unique_new_email(self, db):
        """Test validating unique email for new user"""
        # Arrange
        email = "newemail@example.com"
        
        # Act & Assert - should not raise
        validate_email_unique(email)

    def test_validate_email_unique_existing_email(self, user, db):
        """Test validating email that already exists"""
        # Arrange
        email = user.email
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Email already exists"):
            validate_email_unique(email)

    def test_validate_email_unique_exclude_user(self, user, db):
        """Test validating email excluding specific user"""
        # Arrange
        email = user.email
        
        # Act & Assert - should not raise
        validate_email_unique(email, exclude_user_id=user.id)

    def test_validate_username_unique_new_username(self, db):
        """Test validating unique username for new user"""
        # Arrange
        username = "newusername"
        
        # Act & Assert - should not raise
        validate_username_unique(username)

    def test_validate_username_unique_existing_username(self, user, db):
        """Test validating username that already exists"""
        # Arrange
        username = user.username
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Username already exists"):
            validate_username_unique(username)

    def test_validate_username_unique_exclude_user(self, user, db):
        """Test validating username excluding specific user"""
        # Arrange
        username = user.username
        
        # Act & Assert - should not raise
        validate_username_unique(username, exclude_user_id=user.id)

    def test_validate_profile_data_valid(self, db):
        """Test validating valid profile data"""
        # Arrange
        data = {
            'about': 'Short bio',
            'expertise': 'Python, Django',
        }
        
        # Act & Assert - should not raise
        validate_profile_data(data)

    def test_validate_profile_data_about_too_long(self, db):
        """Test validating profile with about section too long"""
        # Arrange
        data = {
            'about': 'x' * 5001,
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="About section too long"):
            validate_profile_data(data)

    def test_validate_profile_data_expertise_too_long(self, db):
        """Test validating profile with expertise section too long"""
        # Arrange
        data = {
            'expertise': 'x' * 2001,
        }
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Expertise section too long"):
            validate_profile_data(data)

    def test_validate_password_strength_valid(self, db):
        """Test validating strong password"""
        # Arrange
        password = "StrongPass123"
        
        # Act & Assert - should not raise
        validate_password_strength(password)

    def test_validate_password_strength_too_short(self, db):
        """Test validating password that is too short"""
        # Arrange
        password = "Short1"
        
        # Act & Assert
        with pytest.raises(ValidationError, match="at least 8 characters"):
            validate_password_strength(password)

    def test_validate_password_strength_no_digit(self, db):
        """Test validating password without digit"""
        # Arrange
        password = "NoDigitPass"
        
        # Act & Assert
        with pytest.raises(ValidationError, match="at least one digit"):
            validate_password_strength(password)

    def test_validate_password_strength_no_uppercase(self, db):
        """Test validating password without uppercase"""
        # Arrange
        password = "nouppercase123"
        
        # Act & Assert
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength(password)
