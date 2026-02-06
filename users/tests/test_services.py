"""
Tests for user services
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError

from users.services.user_service import UserService
from users.services.profile_service import ProfileService
from users.services.entry_service import EmploymentService, EducationService
from users.services.export_service import ExportService
from users.models import PublicStaffProfile, EmploymentEntry, EducationEntry

User = get_user_model()


class TestUserService:
    """Tests for UserService"""

    def test_authenticate_user_success(self, db):
        """Test successful user authentication"""
        # Arrange
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Act
        authenticated = UserService.authenticate_user('testuser', 'testpass123')
        
        # Assert
        assert authenticated is not None
        assert authenticated.username == 'testuser'

    def test_authenticate_user_invalid_credentials(self, db):
        """Test authentication with invalid credentials"""
        # Arrange
        User.objects.create_user(username='testuser', password='testpass123')
        
        # Act
        authenticated = UserService.authenticate_user('testuser', 'wrongpass')
        
        # Assert
        assert authenticated is None

    def test_authenticate_user_missing_credentials(self, db):
        """Test authentication with missing credentials"""
        # Act & Assert
        with pytest.raises(ValidationError, match='Username and password are required'):
            UserService.authenticate_user('', 'password')

    @patch('users.services.user_service.login')
    def test_login_user(self, mock_login, user, db):
        """Test logging in user"""
        # Arrange
        request = Mock()
        
        # Act
        UserService.login_user(request, user)
        
        # Assert
        mock_login.assert_called_once_with(request, user)

    @patch('users.services.user_service.logout')
    def test_logout_user_with_url(self, mock_logout, user, db):
        """Test logging out user with logout URL"""
        # Arrange
        request = Mock(user=user, META={'HTTP_X_LOGOUT_URL': 'https://example.com/logout'})
        
        # Act
        result = UserService.logout_user(request)
        
        # Assert
        mock_logout.assert_called_once_with(request)
        assert result == {'logoutUrl': 'https://example.com/logout'}

    @patch('users.services.user_service.logout')
    def test_logout_user_without_url(self, mock_logout, user, db):
        """Test logging out user without logout URL"""
        # Arrange
        request = Mock(user=user, META={})
        
        # Act
        result = UserService.logout_user(request)
        
        # Assert
        mock_logout.assert_called_once_with(request)
        assert result == {}

    def test_change_password_success(self, db):
        """Test successful password change"""
        # Arrange
        user = User.objects.create_user(username='testuser', password='oldpass123')
        
        # Act
        UserService.change_password(user, 'oldpass123', 'newpass123')
        
        # Assert
        user.refresh_from_db()
        assert user.check_password('newpass123')

    def test_change_password_incorrect_old(self, db):
        """Test password change with incorrect old password"""
        # Arrange
        user = User.objects.create_user(username='testuser', password='oldpass123')
        
        # Act & Assert
        with pytest.raises(ValidationError, match='Incorrect old password'):
            UserService.change_password(user, 'wrongpass', 'newpass123')

    def test_list_users_no_filters(self, user, db):
        """Test listing users without filters"""
        # Act
        users = UserService.list_users()
        
        # Assert
        assert users.count() >= 1
        assert user in users

    def test_list_users_with_search(self, user, db):
        """Test listing users with search term"""
        # Act
        users = UserService.list_users(filters={'search': 'Test'})
        
        # Assert
        assert users.count() >= 1
        assert user in users

    def test_list_users_with_filters(self, user, staff_user, db):
        """Test listing users with filters"""
        # Act
        staff_users = UserService.list_users(filters={'is_staff': True})
        
        # Assert
        assert staff_user in staff_users
        assert user not in staff_users

    def test_get_user_success(self, user, db):
        """Test getting user by ID"""
        # Act
        retrieved = UserService.get_user(user.id)
        
        # Assert
        assert retrieved.id == user.id
        assert retrieved.username == user.username

    def test_get_user_not_found(self, db):
        """Test getting non-existent user"""
        # Act & Assert
        with pytest.raises(NotFound, match='User 99999 not found'):
            UserService.get_user(99999)

    def test_create_user(self, db):
        """Test creating user"""
        # Arrange
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        
        # Act
        user = UserService.create_user(data)
        
        # Assert
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.first_name == 'New'
        assert user.check_password('testpass123')

    def test_update_user(self, user, db):
        """Test updating user"""
        # Arrange
        data = {'first_name': 'Updated', 'last_name': 'Name'}
        
        # Act
        updated = UserService.update_user(user.id, data)
        
        # Assert
        assert updated.first_name == 'Updated'
        assert updated.last_name == 'Name'

    def test_update_user_password(self, user, db):
        """Test updating user password"""
        # Arrange
        data = {'password': 'newpass123'}
        
        # Act
        updated = UserService.update_user(user.id, data)
        
        # Assert
        assert updated.check_password('newpass123')

    def test_delete_user(self, user, db):
        """Test deleting user"""
        # Arrange
        user_id = user.id
        
        # Act
        UserService.delete_user(user_id)
        
        # Assert
        assert not User.objects.filter(id=user_id).exists()

    def test_toggle_active(self, user, db):
        """Test toggling user active status"""
        # Arrange
        original_status = user.is_active
        
        # Act
        updated = UserService.toggle_active(user.id)
        
        # Assert
        assert updated.is_active != original_status

    def test_switch_admin(self, user, db):
        """Test toggling user admin status"""
        # Arrange
        original_status = user.is_superuser
        
        # Act
        updated = UserService.switch_admin(user.id)
        
        # Assert
        assert updated.is_superuser != original_status

    def test_check_email_exists_true(self, user, db):
        """Test checking existing email"""
        # Act
        exists = UserService.check_email_exists(user.email)
        
        # Assert
        assert exists is True

    def test_check_email_exists_false(self, db):
        """Test checking non-existent email"""
        # Act
        exists = UserService.check_email_exists('nonexistent@example.com')
        
        # Assert
        assert exists is False

    def test_check_username_exists_true(self, user, db):
        """Test checking existing username"""
        # Act
        exists = UserService.check_username_exists(user.username)
        
        # Assert
        assert exists is True

    def test_check_username_exists_false(self, db):
        """Test checking non-existent username"""
        # Act
        exists = UserService.check_username_exists('nonexistent')
        
        # Assert
        assert exists is False

    def test_list_users_with_business_area_filter(self, user, business_area, user_work, db):
        """Test listing users filtered by business area"""
        # Act
        users = UserService.list_users(filters={'business_area': business_area.id})
        
        # Assert
        assert users.count() >= 1
        assert user in users

    def test_list_users_with_is_active_filter(self, user_factory, db):
        """Test listing users with is_active filter"""
        # Arrange
        active_user = user_factory(is_active=True)
        inactive_user = user_factory(is_active=False)
        
        # Act
        users = UserService.list_users(filters={'is_active': True})
        
        # Assert
        assert active_user in users
        assert inactive_user not in users

    def test_list_users_with_is_staff_filter(self, user_factory, db):
        """Test listing users with is_staff filter"""
        # Arrange
        staff_user = user_factory(is_staff=True)
        regular_user = user_factory(is_staff=False)
        
        # Act
        users = UserService.list_users(filters={'is_staff': True})
        
        # Assert
        assert staff_user in users
        assert regular_user not in users

    def test_list_users_with_is_superuser_filter(self, user_factory, db):
        """Test listing users with is_superuser filter"""
        # Arrange
        superuser = user_factory(is_superuser=True)
        regular_user = user_factory(is_superuser=False)
        
        # Act
        users = UserService.list_users(filters={'is_superuser': True})
        
        # Assert
        assert superuser in users
        assert regular_user not in users


class TestProfileService:
    """Tests for ProfileService"""

    def test_list_staff_profiles_no_filters(self, staff_profile, db):
        """Test listing staff profiles without filters"""
        # Act
        profiles = ProfileService.list_staff_profiles()
        
        # Assert
        assert profiles.count() >= 1
        assert staff_profile in profiles

    def test_list_staff_profiles_with_search(self, staff_profile, db):
        """Test listing staff profiles with search"""
        # Act
        profiles = ProfileService.list_staff_profiles(search='Test')
        
        # Assert
        assert profiles.count() >= 1
        assert staff_profile in profiles

    def test_list_staff_profiles_with_filters(self, staff_profile, db):
        """Test listing staff profiles with filters"""
        # Arrange
        staff_profile.is_hidden = False
        staff_profile.save()
        
        # Act
        profiles = ProfileService.list_staff_profiles(filters={'is_hidden': False})
        
        # Assert
        assert staff_profile in profiles

    def test_get_staff_profile_success(self, staff_profile, db):
        """Test getting staff profile by ID"""
        # Act
        retrieved = ProfileService.get_staff_profile(staff_profile.id)
        
        # Assert
        assert retrieved.id == staff_profile.id

    def test_get_staff_profile_not_found(self, db):
        """Test getting non-existent staff profile"""
        # Act & Assert
        with pytest.raises(NotFound, match='Profile 99999 not found'):
            ProfileService.get_staff_profile(99999)

    def test_get_staff_profile_by_user_success(self, staff_profile, user, db):
        """Test getting staff profile by user ID"""
        # Act
        retrieved = ProfileService.get_staff_profile_by_user(user.id)
        
        # Assert
        assert retrieved.id == staff_profile.id

    def test_get_staff_profile_by_user_not_found(self, db):
        """Test getting staff profile for user without profile"""
        # Arrange
        user = User.objects.create_user(username='noprofile')
        
        # Act
        result = ProfileService.get_staff_profile_by_user(user.id)
        
        # Assert
        assert result is None

    def test_create_staff_profile(self, user, db):
        """Test creating staff profile"""
        # Arrange
        data = {
            'about': 'Test about',
            'expertise': 'Test expertise',
            'is_hidden': False,
        }
        
        # Act
        profile = ProfileService.create_staff_profile(user.id, data)
        
        # Assert
        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.about == 'Test about'
        assert profile.is_hidden is False

    def test_create_staff_profile_duplicate(self, staff_profile, user, db):
        """Test creating duplicate staff profile"""
        # Arrange
        data = {'about': 'Test'}
        
        # Act & Assert
        with pytest.raises(ValidationError, match='Profile already exists'):
            ProfileService.create_staff_profile(user.id, data)

    def test_update_staff_profile(self, staff_profile, db):
        """Test updating staff profile"""
        # Arrange
        data = {'about': 'Updated about'}
        
        # Act
        updated = ProfileService.update_staff_profile(staff_profile.id, data)
        
        # Assert
        assert updated.about == 'Updated about'

    def test_delete_staff_profile(self, staff_profile, db):
        """Test deleting staff profile"""
        # Arrange
        profile_id = staff_profile.id
        
        # Act
        ProfileService.delete_staff_profile(profile_id)
        
        # Assert
        assert not PublicStaffProfile.objects.filter(id=profile_id).exists()

    def test_toggle_visibility(self, staff_profile, db):
        """Test toggling profile visibility"""
        # Arrange
        original_status = staff_profile.is_hidden
        
        # Act
        updated = ProfileService.toggle_visibility(staff_profile.id)
        
        # Assert
        assert updated.is_hidden != original_status

    def test_get_active_staff_emails(self, staff_profile, db):
        """Test getting active staff emails"""
        # Arrange
        staff_profile.is_hidden = False
        staff_profile.save()
        
        # Act
        profiles = ProfileService.get_active_staff_emails()
        
        # Assert
        assert profiles.count() >= 1
        assert staff_profile in profiles

    def test_check_staff_profile_exists_true(self, staff_profile, user, db):
        """Test checking existing staff profile"""
        # Act
        result = ProfileService.check_staff_profile_exists(user.id)
        
        # Assert
        assert result['exists'] is True
        assert result['profile'] == staff_profile

    def test_check_staff_profile_exists_false(self, db):
        """Test checking non-existent staff profile"""
        # Arrange
        user = User.objects.create_user(username='noprofile')
        
        # Act
        result = ProfileService.check_staff_profile_exists(user.id)
        
        # Assert
        assert result['exists'] is False
        assert result['profile'] is None

    def test_get_user_profile_success(self, user_profile, db):
        """Test getting user profile by ID"""
        # Act
        retrieved = ProfileService.get_user_profile(user_profile.id)
        
        # Assert
        assert retrieved.id == user_profile.id

    def test_get_user_profile_not_found(self, db):
        """Test getting non-existent user profile"""
        # Act & Assert
        with pytest.raises(NotFound, match='User profile 99999 not found'):
            ProfileService.get_user_profile(99999)

    def test_update_user_profile(self, user_profile, db):
        """Test updating user profile"""
        # Arrange
        data = {'title': 'prof'}
        
        # Act
        updated = ProfileService.update_user_profile(user_profile.id, data)
        
        # Assert
        assert updated.title == 'prof'

    def test_update_personal_information(self, user, db):
        """Test updating user personal information"""
        # Arrange
        data = {'first_name': 'Updated'}
        
        # Act
        updated = ProfileService.update_personal_information(user.id, data)
        
        # Assert
        assert updated.first_name == 'Updated'

    def test_update_personal_information_not_found(self, db):
        """Test updating personal information for non-existent user"""
        # Arrange
        data = {'first_name': 'Updated'}
        
        # Act & Assert
        with pytest.raises(NotFound, match='User 99999 not found'):
            ProfileService.update_personal_information(99999, data)

    def test_list_staff_profiles_with_business_area_filter(self, staff_profile, business_area, user_work, db):
        """Test listing staff profiles filtered by business area"""
        # Act
        profiles = ProfileService.list_staff_profiles(filters={'business_area': business_area.id})
        
        # Assert
        assert profiles.count() >= 1
        assert staff_profile in profiles

    def test_list_user_profiles_with_user_filter(self, user_profile, user, db):
        """Test listing user profiles filtered by user"""
        # Act
        profiles = ProfileService.list_user_profiles(filters={'user': user.id})
        
        # Assert
        assert profiles.count() >= 1
        assert user_profile in profiles


class TestEntryService:
    """Tests for EmploymentService and EducationService"""

    def test_list_employment(self, employment_entry, staff_profile, db):
        """Test listing employment entries"""
        # Act
        entries = EmploymentService.list_employment(staff_profile.id)
        
        # Assert
        assert entries.count() >= 1
        assert employment_entry in entries

    def test_get_employment_success(self, employment_entry, db):
        """Test getting employment entry by ID"""
        # Act
        retrieved = EmploymentService.get_employment(employment_entry.id)
        
        # Assert
        assert retrieved.id == employment_entry.id

    def test_get_employment_not_found(self, db):
        """Test getting non-existent employment entry"""
        # Act & Assert
        with pytest.raises(NotFound, match='Employment entry 99999 not found'):
            EmploymentService.get_employment(99999)

    def test_create_employment(self, staff_profile, db):
        """Test creating employment entry"""
        # Arrange
        data = {
            'position_title': 'Test Position',
            'employer': 'Test Org',
            'start_year': 2020,
            'end_year': 2023,
            'section': 'Test Section',
        }
        
        # Act
        entry = EmploymentService.create_employment(staff_profile.id, data)
        
        # Assert
        assert entry.id is not None
        assert entry.position_title == 'Test Position'
        assert entry.start_year == 2020

    def test_update_employment(self, employment_entry, db):
        """Test updating employment entry"""
        # Arrange
        data = {'position_title': 'Updated Position'}
        
        # Act
        updated = EmploymentService.update_employment(employment_entry.id, data)
        
        # Assert
        assert updated.position_title == 'Updated Position'

    def test_delete_employment(self, employment_entry, db):
        """Test deleting employment entry"""
        # Arrange
        entry_id = employment_entry.id
        
        # Act
        EmploymentService.delete_employment(entry_id)
        
        # Assert
        assert not EmploymentEntry.objects.filter(id=entry_id).exists()

    def test_list_education(self, education_entry, staff_profile, db):
        """Test listing education entries"""
        # Act
        entries = EducationService.list_education(staff_profile.id)
        
        # Assert
        assert entries.count() >= 1
        assert education_entry in entries

    def test_get_education_success(self, education_entry, db):
        """Test getting education entry by ID"""
        # Act
        retrieved = EducationService.get_education(education_entry.id)
        
        # Assert
        assert retrieved.id == education_entry.id

    def test_get_education_not_found(self, db):
        """Test getting non-existent education entry"""
        # Act & Assert
        with pytest.raises(NotFound, match='Education entry 99999 not found'):
            EducationService.get_education(99999)

    def test_create_education(self, staff_profile, db):
        """Test creating education entry"""
        # Arrange
        data = {
            'qualification_name': 'Test Degree',
            'institution': 'Test University',
            'end_year': 2019,
            'location': 'Test City',
        }
        
        # Act
        entry = EducationService.create_education(staff_profile.id, data)
        
        # Assert
        assert entry.id is not None
        assert entry.qualification_name == 'Test Degree'
        assert entry.end_year == 2019

    def test_update_education(self, education_entry, db):
        """Test updating education entry"""
        # Arrange
        data = {'qualification_name': 'Updated Degree'}
        
        # Act
        updated = EducationService.update_education(education_entry.id, data)
        
        # Assert
        assert updated.qualification_name == 'Updated Degree'

    def test_delete_education(self, education_entry, db):
        """Test deleting education entry"""
        # Arrange
        entry_id = education_entry.id
        
        # Act
        EducationService.delete_education(entry_id)
        
        # Assert
        assert not EducationEntry.objects.filter(id=entry_id).exists()

    def test_create_employment_without_optional_fields(self, staff_profile, db):
        """Test creating employment entry without optional fields"""
        # Arrange
        data = {
            'position_title': 'Test Position',
            'employer': 'Test Org',
            'start_year': 2020,
        }
        
        # Act
        entry = EmploymentService.create_employment(staff_profile.id, data)
        
        # Assert
        assert entry.id is not None
        assert entry.position_title == 'Test Position'
        assert entry.end_year is None
        assert entry.section == ''

    def test_create_education_without_optional_fields(self, staff_profile, db):
        """Test creating education entry without optional fields"""
        # Arrange
        data = {
            'qualification_name': 'Test Degree',
            'institution': 'Test University',
            'end_year': 2019,
        }
        
        # Act
        entry = EducationService.create_education(staff_profile.id, data)
        
        # Assert
        assert entry.id is not None
        assert entry.qualification_name == 'Test Degree'
        assert entry.location == ''

    def test_list_employment_ordering(self, staff_profile, db):
        """Test employment entries are ordered by start_year and end_year descending"""
        # Arrange
        EmploymentEntry.objects.create(
            public_profile=staff_profile,
            position_title='Position 1',
            employer='Org 1',
            start_year=2015,
            end_year=2018,
        )
        EmploymentEntry.objects.create(
            public_profile=staff_profile,
            position_title='Position 2',
            employer='Org 2',
            start_year=2020,
            end_year=2023,
        )
        EmploymentEntry.objects.create(
            public_profile=staff_profile,
            position_title='Position 3',
            employer='Org 3',
            start_year=2020,
            end_year=2021,
        )
        
        # Act
        entries = EmploymentService.list_employment(staff_profile.id)
        
        # Assert
        assert entries.count() == 3
        # Should be ordered by start_year DESC, then end_year DESC
        assert entries[0].position_title == 'Position 2'  # 2020-2023
        assert entries[1].position_title == 'Position 3'  # 2020-2021
        assert entries[2].position_title == 'Position 1'  # 2015-2018

    def test_list_education_ordering(self, staff_profile, db):
        """Test education entries are ordered by end_year descending"""
        # Arrange
        EducationEntry.objects.create(
            public_profile=staff_profile,
            qualification_name='Degree 1',
            institution='Uni 1',
            end_year=2015,
        )
        EducationEntry.objects.create(
            public_profile=staff_profile,
            qualification_name='Degree 2',
            institution='Uni 2',
            end_year=2020,
        )
        EducationEntry.objects.create(
            public_profile=staff_profile,
            qualification_name='Degree 3',
            institution='Uni 3',
            end_year=2018,
        )
        
        # Act
        entries = EducationService.list_education(staff_profile.id)
        
        # Assert
        assert entries.count() == 3
        # Should be ordered by end_year DESC
        assert entries[0].qualification_name == 'Degree 2'  # 2020
        assert entries[1].qualification_name == 'Degree 3'  # 2018
        assert entries[2].qualification_name == 'Degree 1'  # 2015

    def test_list_employment_empty(self, staff_profile, db):
        """Test listing employment entries when none exist"""
        # Act
        entries = EmploymentService.list_employment(staff_profile.id)
        
        # Assert
        assert entries.count() == 0

    def test_list_education_empty(self, staff_profile, db):
        """Test listing education entries when none exist"""
        # Act
        entries = EducationService.list_education(staff_profile.id)
        
        # Assert
        assert entries.count() == 0

    def test_update_employment_multiple_fields(self, employment_entry, db):
        """Test updating multiple fields in employment entry"""
        # Arrange
        data = {
            'position_title': 'Updated Position',
            'employer': 'Updated Org',
            'section': 'Updated Section',
        }
        
        # Act
        updated = EmploymentService.update_employment(employment_entry.id, data)
        
        # Assert
        assert updated.position_title == 'Updated Position'
        assert updated.employer == 'Updated Org'
        assert updated.section == 'Updated Section'

    def test_update_education_multiple_fields(self, education_entry, db):
        """Test updating multiple fields in education entry"""
        # Arrange
        data = {
            'qualification_name': 'Updated Degree',
            'institution': 'Updated University',
            'location': 'Updated City',
        }
        
        # Act
        updated = EducationService.update_education(education_entry.id, data)
        
        # Assert
        assert updated.qualification_name == 'Updated Degree'
        assert updated.institution == 'Updated University'
        assert updated.location == 'Updated City'


class TestExportService:
    """Tests for ExportService"""

    def test_generate_staff_csv(self, staff_profile, db):
        """Test generating staff CSV export"""
        # Arrange
        staff_profile.is_hidden = False
        staff_profile.save()
        
        # Act
        response = ExportService.generate_staff_csv()
        
        # Assert
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']
        
        # Check CSV content
        content = response.content.decode('utf-8')
        assert 'First Name' in content
        assert 'Last Name' in content
        assert 'Email' in content
