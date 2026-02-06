"""
Tests for user models
"""
import pytest
from unittest.mock import Mock, patch
from django.utils import timezone
from datetime import timedelta

from users.models import (
    User,
    UserWork,
    UserProfile,
    KeywordTag,
    EmploymentEntry,
    EducationEntry,
    DOIPublication,
    PublicStaffProfile,
)


class TestUserModel:
    """Tests for User model"""

    def test_user_creation(self, db):
        """Test creating a user"""
        # Arrange & Act
        user = User.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
        )
        
        # Assert
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'

    def test_user_str_representation(self, user, db):
        """Test user string representation"""
        # Act
        result = str(user)
        
        # Assert
        assert 'Test' in result
        assert 'User' in result
        assert 'testuser' in result

    def test_user_save_auto_populates_display_names(self, db):
        """Test that save() auto-populates display names"""
        # Arrange
        user = User(
            username='testuser',
            first_name='John',
            last_name='Doe',
        )
        
        # Act
        user.save()
        
        # Assert
        assert user.display_first_name == 'John'
        assert user.display_last_name == 'Doe'

    def test_user_save_preserves_existing_display_names(self, db):
        """Test that save() preserves existing display names"""
        # Arrange
        user = User(
            username='testuser',
            first_name='John',
            last_name='Doe',
            display_first_name='Jöhn',
            display_last_name='Döe',
        )
        
        # Act
        user.save()
        
        # Assert
        assert user.display_first_name == 'Jöhn'
        assert user.display_last_name == 'Döe'

    def test_get_formatted_name_with_initials(self, user, user_profile, db):
        """Test formatted name with middle initials"""
        # Arrange
        user_profile.middle_initials = 'A B'
        user_profile.save()
        
        # Act
        result = user.get_formatted_name()
        
        # Assert
        assert 'User' in result
        assert 'T.' in result
        assert 'A.' in result
        assert 'B.' in result

    def test_get_formatted_name_without_initials(self, user, user_profile, db):
        """Test formatted name without middle initials"""
        # Arrange
        user_profile.middle_initials = None
        user_profile.save()
        
        # Act
        result = user.get_formatted_name()
        
        # Assert
        assert 'User' in result
        assert 'T.' in result

    def test_get_image_with_avatar(self, user, db):
        """Test getting user image when avatar exists"""
        # Arrange
        from medias.models import UserAvatar
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        avatar = UserAvatar.objects.create(
            user=user,
            file=SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')
        )
        
        # Act
        result = user.get_image()
        
        # Assert
        assert result is not None
        assert 'file' in result

    def test_get_image_without_avatar(self, user, db):
        """Test getting user image when no avatar exists"""
        # Act
        result = user.get_image()
        
        # Assert
        assert result is None

    def test_get_caretakers(self, user, user_factory, db):
        """Test getting active caretakers"""
        # Arrange
        from caretakers.models import Caretaker
        caretaker_user = user_factory()
        
        # Create active caretaker
        Caretaker.objects.create(
            user=user,
            caretaker=caretaker_user,
            end_date=None,
        )
        
        # Act
        caretakers = user.get_caretakers()
        
        # Assert
        assert caretakers.count() == 1

    def test_get_caretakers_excludes_expired(self, user, user_factory, db):
        """Test that get_caretakers excludes expired caretakers"""
        # Arrange
        from caretakers.models import Caretaker
        caretaker_user = user_factory()
        
        # Create expired caretaker
        Caretaker.objects.create(
            user=user,
            caretaker=caretaker_user,
            end_date=timezone.now() - timedelta(days=1),
        )
        
        # Act
        caretakers = user.get_caretakers()
        
        # Assert
        assert caretakers.count() == 0

    def test_get_all_caretakers(self, user, user_factory, db):
        """Test getting all caretakers including expired"""
        # Arrange
        from caretakers.models import Caretaker
        caretaker_user = user_factory()
        
        # Create expired caretaker
        Caretaker.objects.create(
            user=user,
            caretaker=caretaker_user,
            end_date=timezone.now() - timedelta(days=1),
        )
        
        # Act
        caretakers = user.get_all_caretakers()
        
        # Assert
        assert caretakers.count() == 1

    def test_get_caretaking_for(self, user, user_factory, db):
        """Test getting users this user is caretaking for"""
        # Arrange
        from caretakers.models import Caretaker
        other_user = user_factory()
        
        # Create caretaking relationship
        Caretaker.objects.create(
            user=other_user,
            caretaker=user,
            end_date=None,
        )
        
        # Act
        caretaking = user.get_caretaking_for()
        
        # Assert
        assert caretaking.count() == 1

    def test_get_caretaker_data(self, user, db):
        """Test getting caretaker data"""
        # Act
        data = user.get_caretaker_data()
        
        # Assert
        assert data is not None
        assert data['id'] == user.pk
        assert data['display_first_name'] == user.display_first_name
        assert data['display_last_name'] == user.display_last_name
        assert data['is_superuser'] == user.is_superuser
        assert data['email'] == user.email

    def test_get_caretaker_data_prevents_recursion(self, user, db):
        """Test that get_caretaker_data prevents infinite recursion"""
        # Act
        data = user.get_caretaker_data(current_path=[user.pk])
        
        # Assert
        assert data is None


class TestUserWorkModel:
    """Tests for UserWork model"""

    def test_user_work_creation(self, user, business_area, db):
        """Test creating user work"""
        # Arrange & Act
        work = UserWork.objects.create(
            user=user,
            business_area=business_area,
            role='DBCA Member',
        )
        
        # Assert
        assert work.user == user
        assert work.business_area == business_area
        assert work.role == 'DBCA Member'

    def test_user_work_str_representation(self, user_work, db):
        """Test user work string representation"""
        # Act
        result = str(user_work)
        
        # Assert
        assert 'Work Detail' in result
        assert str(user_work.user) in result

    def test_user_work_role_choices(self, db):
        """Test user work role choices"""
        # Act
        choices = UserWork.RoleChoices
        
        # Assert
        assert hasattr(choices, 'ECODEV')
        assert hasattr(choices, 'EXECDIR')
        assert hasattr(choices, 'BALEAD')
        assert hasattr(choices, 'ADMIN')
        assert hasattr(choices, 'DBCA')


class TestUserProfileModel:
    """Tests for UserProfile model"""

    def test_user_profile_creation(self, user, db):
        """Test creating user profile"""
        # Arrange & Act
        profile = UserProfile.objects.create(
            user=user,
            title='dr',
            middle_initials='A',
        )
        
        # Assert
        assert profile.user == user
        assert profile.title == 'dr'
        assert profile.middle_initials == 'A'

    def test_user_profile_str_representation(self, user_profile, db):
        """Test user profile string representation"""
        # Act
        result = str(user_profile)
        
        # Assert
        assert 'Profile' in result
        assert user_profile.user.username in result

    def test_user_profile_title_choices(self, db):
        """Test user profile title choices"""
        # Act
        choices = UserProfile.TitleChoices
        
        # Assert
        assert hasattr(choices, 'MR')
        assert hasattr(choices, 'MS')
        assert hasattr(choices, 'DR')
        assert hasattr(choices, 'PROF')


class TestKeywordTagModel:
    """Tests for KeywordTag model"""

    def test_keyword_tag_creation(self, db):
        """Test creating keyword tag"""
        # Arrange & Act
        tag = KeywordTag.objects.create(name='Python')
        
        # Assert
        assert tag.name == 'Python'

    def test_keyword_tag_str_representation(self, db):
        """Test keyword tag string representation"""
        # Arrange
        tag = KeywordTag.objects.create(name='Django')
        
        # Act
        result = str(tag)
        
        # Assert
        assert result == 'Django'

    def test_keyword_tag_unique_name(self, db):
        """Test keyword tag name uniqueness"""
        # Arrange
        KeywordTag.objects.create(name='Python')
        
        # Act & Assert
        with pytest.raises(Exception):  # IntegrityError
            KeywordTag.objects.create(name='Python')


class TestEmploymentEntryModel:
    """Tests for EmploymentEntry model"""

    def test_employment_entry_creation(self, staff_profile, db):
        """Test creating employment entry"""
        # Arrange & Act
        entry = EmploymentEntry.objects.create(
            public_profile=staff_profile,
            position_title='Software Developer',
            start_year=2020,
            end_year=2023,
            section='IT',
            employer='DBCA',
        )
        
        # Assert
        assert entry.public_profile == staff_profile
        assert entry.position_title == 'Software Developer'
        assert entry.start_year == 2020
        assert entry.end_year == 2023

    def test_employment_entry_str_representation(self, employment_entry, db):
        """Test employment entry string representation"""
        # Act
        result = str(employment_entry)
        
        # Assert
        assert employment_entry.position_title in result
        assert employment_entry.employer in result
        assert str(employment_entry.start_year) in result


class TestEducationEntryModel:
    """Tests for EducationEntry model"""

    def test_education_entry_creation(self, staff_profile, db):
        """Test creating education entry"""
        # Arrange & Act
        entry = EducationEntry.objects.create(
            public_profile=staff_profile,
            qualification_name='Bachelor of Science',
            end_year=2019,
            institution='University of Test',
            location='Perth',
        )
        
        # Assert
        assert entry.public_profile == staff_profile
        assert entry.qualification_name == 'Bachelor of Science'
        assert entry.end_year == 2019
        assert entry.institution == 'University of Test'

    def test_education_entry_str_representation(self, education_entry, db):
        """Test education entry string representation"""
        # Act
        result = str(education_entry)
        
        # Assert
        assert education_entry.qualification_name in result
        assert education_entry.institution in result
        assert str(education_entry.end_year) in result


class TestDOIPublicationModel:
    """Tests for DOIPublication model"""

    def test_doi_publication_creation(self, user, db):
        """Test creating DOI publication"""
        # Arrange & Act
        pub = DOIPublication.objects.create(
            user=user,
            doi='10.1234/test.doi',
        )
        
        # Assert
        assert pub.user == user
        assert pub.doi == '10.1234/test.doi'

    def test_doi_publication_str_representation(self, user, db):
        """Test DOI publication string representation"""
        # Arrange
        pub = DOIPublication.objects.create(
            user=user,
            doi='10.1234/test.doi',
        )
        
        # Act
        result = str(pub)
        
        # Assert
        assert str(pub.pk) in result
        assert str(user) in result
        assert pub.doi in result


class TestPublicStaffProfileModel:
    """Tests for PublicStaffProfile model"""

    def test_staff_profile_creation(self, user, db):
        """Test creating staff profile"""
        # Arrange & Act
        profile = PublicStaffProfile.objects.create(
            user=user,
            about='Test about',
            expertise='Test expertise',
            public_email='public@example.com',
            public_email_on=True,
        )
        
        # Assert
        assert profile.user == user
        assert profile.about == 'Test about'
        assert profile.expertise == 'Test expertise'
        assert profile.public_email == 'public@example.com'
        assert profile.public_email_on is True

    def test_staff_profile_str_representation(self, staff_profile, db):
        """Test staff profile string representation"""
        # Act
        result = str(staff_profile)
        
        # Assert
        assert 'Staff Profile' in result
        assert staff_profile.user.first_name in result
        assert staff_profile.user.last_name in result

    def test_staff_profile_title_choices(self, db):
        """Test staff profile title choices"""
        # Act
        choices = PublicStaffProfile.TitleChoices
        
        # Assert
        assert hasattr(choices, 'MR')
        assert hasattr(choices, 'MS')
        assert hasattr(choices, 'DR')
        assert hasattr(choices, 'PROF')

    def test_staff_profile_keyword_tags(self, staff_profile, db):
        """Test staff profile keyword tags relationship"""
        # Arrange
        tag1 = KeywordTag.objects.create(name='Python')
        tag2 = KeywordTag.objects.create(name='Django')
        
        # Act
        staff_profile.keyword_tags.add(tag1, tag2)
        
        # Assert
        assert staff_profile.keyword_tags.count() == 2
        assert tag1 in staff_profile.keyword_tags.all()
        assert tag2 in staff_profile.keyword_tags.all()

    @patch('users.models.requests.get')
    def test_get_it_asset_data_success(self, mock_get, staff_profile, db):
        """Test getting IT asset data successfully"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 123,
                'email': staff_profile.user.email,
                'title': 'Test Title',
                'division': 'Test Division',
                'unit': 'Test Unit',
                'location': 'Test Location',
            }
        ]
        mock_get.return_value = mock_response
        
        # Act
        result = staff_profile.get_it_asset_data()
        
        # Assert
        assert result is not None
        assert result['id'] == 123
        assert result['title'] == 'Test Title'
        assert result['division'] == 'Test Division'

    @patch('users.models.requests.get')
    def test_get_it_asset_data_failure(self, mock_get, staff_profile, db):
        """Test getting IT asset data when API fails"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response
        
        # Act
        result = staff_profile.get_it_asset_data()
        
        # Assert
        assert result is None

    @patch('users.models.requests.get')
    def test_get_it_asset_email_success(self, mock_get, staff_profile, db):
        """Test getting IT asset email successfully"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 123,
                'email': 'it.asset@example.com',
            }
        ]
        mock_get.return_value = mock_response
        staff_profile.user.email = 'it.asset@example.com'
        staff_profile.user.save()
        
        # Act
        result = staff_profile.get_it_asset_email()
        
        # Assert
        assert result == 'it.asset@example.com'

    @patch('users.models.requests.get')
    def test_get_it_asset_email_failure(self, mock_get, staff_profile, db):
        """Test getting IT asset email when API fails"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response
        
        # Act
        result = staff_profile.get_it_asset_email()
        
        # Assert
        assert result is None
