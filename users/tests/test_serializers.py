"""
Tests for users serializers
"""
import pytest
from django.contrib.auth import get_user_model

from users.serializers import (
    # Base serializers
    UserSerializer,
    TinyUserSerializer,
    PrivateTinyUserSerializer,
    MiniUserSerializer,
    BasicUserSerializer,
    StaffProfileEmailListSerializer,
    TinyUserWorkSerializer,
    UserWorkSerializer,
    # Profile serializers
    TinyUserProfileSerializer,
    UserProfileSerializer,
    ProfilePageSerializer,
    # Staff profile serializers
    KeywordTagSerializer,
    TinyStaffProfileSerializer,
    StaffProfileCreationSerializer,
    StaffProfileHeroSerializer,
    StaffProfileOverviewSerializer,
    StaffProfileCVSerializer,
    StaffProfileSerializer,
    # Entry serializers
    EmploymentEntrySerializer,
    EmploymentEntryCreationSerializer,
    EducationEntrySerializer,
    EducationEntryCreationSerializer,
    # Update serializers
    UpdatePISerializer,
    UpdateProfileSerializer,
    UpdateMembershipSerializer,
    UserWorkAffiliationUpdateSerializer,
)
from users.models import KeywordTag

User = get_user_model()


class TestUserSerializer:
    """Tests for UserSerializer"""

    def test_serialize_user(self, user, db):
        """Test serializing user"""
        # Act
        serializer = UserSerializer(user)
        
        # Assert
        assert serializer.data['id'] == user.id
        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert 'password' not in serializer.data


class TestTinyUserSerializer:
    """Tests for TinyUserSerializer"""

    def test_serialize_user_basic(self, user, db):
        """Test serializing user with basic fields"""
        # Act
        serializer = TinyUserSerializer(user)
        
        # Assert
        assert serializer.data['id'] == user.id
        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert serializer.data['name'] == f"{user.display_first_name} {user.display_last_name}"

    def test_serialize_user_with_avatar(self, user, db):
        """Test serializing user with avatar"""
        # Arrange
        from medias.models import UserAvatar
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        avatar = UserAvatar.objects.create(
            user=user,
            file=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        
        # Act
        serializer = TinyUserSerializer(user)
        
        # Assert
        assert serializer.data['image'] is not None

    def test_serialize_user_without_avatar(self, user, db):
        """Test serializing user without avatar"""
        # Act
        serializer = TinyUserSerializer(user)
        
        # Assert
        assert serializer.data['image'] is None

    def test_serialize_user_with_work(self, user, user_work, db):
        """Test serializing user with work details"""
        # Act
        serializer = TinyUserSerializer(user)
        
        # Assert
        assert serializer.data['business_area'] is not None
        assert serializer.data['business_area']['id'] == user_work.business_area.id

    def test_serialize_user_without_work(self, user, db):
        """Test serializing user without work details"""
        # Act
        serializer = TinyUserSerializer(user)
        
        # Assert
        assert serializer.data['affiliation'] is None
        assert serializer.data['business_area'] is None


class TestPrivateTinyUserSerializer:
    """Tests for PrivateTinyUserSerializer"""

    def test_serialize_user_excludes_sensitive_fields(self, user, db):
        """Test serializing user excludes sensitive fields"""
        # Act
        serializer = PrivateTinyUserSerializer(user)
        
        # Assert
        assert 'password' not in serializer.data
        assert 'is_superuser' not in serializer.data
        assert 'is_staff' not in serializer.data
        assert 'id' not in serializer.data


class TestMiniUserSerializer:
    """Tests for MiniUserSerializer"""

    def test_serialize_user_with_caretakers(self, user, db):
        """Test serializing user with caretakers"""
        # Arrange
        from caretakers.models import Caretaker
        caretaker = User.objects.create(
            username='caretaker',
            email='caretaker@example.com',
            first_name='Care',
            last_name='Taker',
        )
        Caretaker.objects.create(user=user, caretaker=caretaker)
        
        # Act
        serializer = MiniUserSerializer(user)
        
        # Assert
        assert len(serializer.data['caretakers']) == 1
        assert serializer.data['caretakers'][0]['name'] == 'Care Taker'


class TestBasicUserSerializer:
    """Tests for BasicUserSerializer"""

    def test_serialize_user_with_work(self, user, user_work, db):
        """Test serializing user with work info"""
        # Act
        serializer = BasicUserSerializer(user)
        
        # Assert
        assert serializer.data['work'] is not None
        assert serializer.data['work']['id'] == user_work.id

    def test_serialize_user_without_work(self, user, db):
        """Test serializing user without work info"""
        # Act
        serializer = BasicUserSerializer(user)
        
        # Assert
        assert serializer.data['work'] is None


class TestStaffProfileEmailListSerializer:
    """Tests for StaffProfileEmailListSerializer"""

    def test_serialize_user_for_email_list(self, user, db):
        """Test serializing user for email list"""
        # Act
        serializer = StaffProfileEmailListSerializer(user)
        
        # Assert
        assert serializer.data['name'] == f"{user.display_first_name} {user.display_last_name}"
        assert serializer.data['email'] == user.email
        assert 'is_active' in serializer.data


class TestTinyUserWorkSerializer:
    """Tests for TinyUserWorkSerializer"""

    def test_serialize_user_work(self, user_work, db):
        """Test serializing user work"""
        # Act
        serializer = TinyUserWorkSerializer(user_work)
        
        # Assert
        assert serializer.data['id'] == user_work.id
        assert serializer.data['business_area']['id'] == user_work.business_area.id


class TestUserWorkSerializer:
    """Tests for UserWorkSerializer"""

    def test_serialize_user_work_full(self, user_work, db):
        """Test serializing full user work"""
        # Act
        serializer = UserWorkSerializer(user_work)
        
        # Assert
        assert serializer.data['id'] == user_work.id
        assert serializer.data['role'] == user_work.role


class TestTinyUserProfileSerializer:
    """Tests for TinyUserProfileSerializer"""

    def test_serialize_user_profile(self, user_profile, db):
        """Test serializing user profile"""
        # Act
        serializer = TinyUserProfileSerializer(user_profile)
        
        # Assert
        assert serializer.data['id'] == user_profile.id
        assert serializer.data['user'] == user_profile.user.id
        assert serializer.data['title'] == user_profile.title


class TestUserProfileSerializer:
    """Tests for UserProfileSerializer"""

    def test_serialize_user_profile_full(self, user_profile, db):
        """Test serializing full user profile"""
        # Act
        serializer = UserProfileSerializer(user_profile)
        
        # Assert
        assert serializer.data['id'] == user_profile.id
        assert serializer.data['title'] == user_profile.title
        assert serializer.data['middle_initials'] == user_profile.middle_initials


class TestProfilePageSerializer:
    """Tests for ProfilePageSerializer"""

    def test_serialize_profile_page(self, user_profile, db):
        """Test serializing profile page"""
        # Act
        serializer = ProfilePageSerializer(user_profile)
        
        # Assert
        assert serializer.data['id'] == user_profile.id
        assert serializer.data['user']['id'] == user_profile.user.id
        assert serializer.data['title'] == user_profile.title

    def test_serialize_profile_page_with_work(self, user_profile, user_work, db):
        """Test serializing profile page with work"""
        # Act
        serializer = ProfilePageSerializer(user_profile)
        
        # Assert
        assert serializer.data['work'] is not None
        assert serializer.data['work']['id'] == user_work.id

    def test_serialize_profile_page_without_work(self, user_profile, db):
        """Test serializing profile page without work"""
        # Act
        serializer = ProfilePageSerializer(user_profile)
        
        # Assert
        assert serializer.data['work'] is None


class TestKeywordTagSerializer:
    """Tests for KeywordTagSerializer"""

    def test_serialize_keyword_tag(self, db):
        """Test serializing keyword tag"""
        # Arrange
        tag = KeywordTag.objects.create(name='Python')
        
        # Act
        serializer = KeywordTagSerializer(tag)
        
        # Assert
        assert serializer.data['id'] == tag.id
        assert serializer.data['name'] == 'Python'


class TestTinyStaffProfileSerializer:
    """Tests for TinyStaffProfileSerializer"""

    def test_serialize_staff_profile(self, staff_profile, db):
        """Test serializing staff profile"""
        # Act
        serializer = TinyStaffProfileSerializer(staff_profile)
        
        # Assert
        assert serializer.data['id'] == staff_profile.id
        assert serializer.data['user']['id'] == staff_profile.user.id
        assert serializer.data['about'] == staff_profile.about

    def test_serialize_staff_profile_with_business_area(self, staff_profile, user_work, db):
        """Test serializing staff profile with business area"""
        # Act
        serializer = TinyStaffProfileSerializer(staff_profile)
        
        # Assert
        assert serializer.data['business_area'] is not None
        assert serializer.data['business_area']['id'] == user_work.business_area.id


class TestStaffProfileCreationSerializer:
    """Tests for StaffProfileCreationSerializer"""

    def test_serialize_staff_profile_creation(self, staff_profile, db):
        """Test serializing staff profile for creation"""
        # Act
        serializer = StaffProfileCreationSerializer(staff_profile)
        
        # Assert
        assert serializer.data['id'] == staff_profile.id
        assert serializer.data['user'] == staff_profile.user.id


class TestStaffProfileHeroSerializer:
    """Tests for StaffProfileHeroSerializer"""

    def test_serialize_staff_profile_hero(self, staff_profile, db):
        """Test serializing staff profile hero section"""
        # Act
        serializer = StaffProfileHeroSerializer(staff_profile)
        
        # Assert
        assert serializer.data['id'] == staff_profile.id
        assert serializer.data['user']['id'] == staff_profile.user.id
        assert serializer.data['about'] == staff_profile.about

    def test_serialize_staff_profile_hero_with_public_email(self, staff_profile, db):
        """Test serializing staff profile hero with public email"""
        # Act
        serializer = StaffProfileHeroSerializer(staff_profile)
        
        # Assert
        # When public_email_on is True, it should show public_email
        assert serializer.data['user']['email'] == staff_profile.public_email

    def test_serialize_staff_profile_hero_without_public_email(self, staff_profile, db):
        """Test serializing staff profile hero without public email"""
        # Arrange
        staff_profile.public_email_on = False
        staff_profile.save()
        
        # Act
        serializer = StaffProfileHeroSerializer(staff_profile)
        
        # Assert
        assert serializer.data['user']['email'] is None

    def test_serialize_staff_profile_hero_with_custom_title(self, staff_profile, user_work, db):
        """Test serializing staff profile hero with custom title"""
        # Act
        serializer = StaffProfileHeroSerializer(staff_profile)
        
        # Assert
        # When custom_title_on is True, it should show custom_title
        assert serializer.data['work'] is not None

    def test_serialize_staff_profile_hero_without_custom_title(self, staff_profile, user_work, db):
        """Test serializing staff profile hero without custom title"""
        # Arrange
        staff_profile.custom_title_on = False
        staff_profile.save()
        
        # Act
        serializer = StaffProfileHeroSerializer(staff_profile)
        
        # Assert
        # When custom_title_on is False, it should show work role
        assert serializer.data['work'] is not None


class TestStaffProfileOverviewSerializer:
    """Tests for StaffProfileOverviewSerializer"""

    def test_serialize_staff_profile_overview(self, staff_profile, db):
        """Test serializing staff profile overview"""
        # Arrange
        tag1 = KeywordTag.objects.create(name='Python')
        tag2 = KeywordTag.objects.create(name='Django')
        staff_profile.keyword_tags.add(tag1, tag2)
        
        # Act
        serializer = StaffProfileOverviewSerializer(staff_profile)
        
        # Assert
        assert serializer.data['id'] == staff_profile.id
        assert serializer.data['expertise'] == staff_profile.expertise
        assert len(serializer.data['keywords']) == 2


class TestStaffProfileCVSerializer:
    """Tests for StaffProfileCVSerializer"""

    def test_serialize_staff_profile_cv(self, staff_profile, employment_entry, education_entry, db):
        """Test serializing staff profile CV"""
        # Act
        serializer = StaffProfileCVSerializer(staff_profile)
        
        # Assert
        assert serializer.data['id'] == staff_profile.id
        assert len(serializer.data['employment_entries']) == 1
        assert len(serializer.data['education_entries']) == 1


class TestStaffProfileSerializer:
    """Tests for StaffProfileSerializer"""

    def test_serialize_staff_profile_full(self, staff_profile, employment_entry, education_entry, db):
        """Test serializing full staff profile"""
        # Arrange
        tag = KeywordTag.objects.create(name='Python')
        staff_profile.keyword_tags.add(tag)
        
        # Act
        serializer = StaffProfileSerializer(staff_profile)
        
        # Assert
        assert serializer.data['id'] == staff_profile.id
        assert serializer.data['user']['id'] == staff_profile.user.id
        assert serializer.data['about'] == staff_profile.about
        assert len(serializer.data['keywords']) == 1
        assert len(serializer.data['employment_entries']) == 1
        assert len(serializer.data['education_entries']) == 1

    def test_serialize_staff_profile_with_public_email(self, staff_profile, db):
        """Test serializing staff profile with public email"""
        # Act
        serializer = StaffProfileSerializer(staff_profile)
        
        # Assert
        # When public_email_on is True and public_email exists, show public_email
        assert serializer.data['user']['email'] == staff_profile.public_email

    def test_serialize_staff_profile_without_public_email(self, staff_profile, db):
        """Test serializing staff profile without public email"""
        # Arrange
        staff_profile.public_email_on = False
        staff_profile.save()
        
        # Act
        serializer = StaffProfileSerializer(staff_profile)
        
        # Assert
        # When public_email_on is False, show user.email
        assert serializer.data['user']['email'] == staff_profile.user.email


class TestEmploymentEntrySerializer:
    """Tests for EmploymentEntrySerializer"""

    def test_serialize_employment_entry(self, employment_entry, db):
        """Test serializing employment entry"""
        # Act
        serializer = EmploymentEntrySerializer(employment_entry)
        
        # Assert
        assert serializer.data['id'] == employment_entry.id
        assert serializer.data['position_title'] == employment_entry.position_title
        assert serializer.data['employer'] == employment_entry.employer


class TestEmploymentEntryCreationSerializer:
    """Tests for EmploymentEntryCreationSerializer"""

    def test_serialize_employment_entry_creation(self, employment_entry, db):
        """Test serializing employment entry for creation"""
        # Act
        serializer = EmploymentEntryCreationSerializer(employment_entry)
        
        # Assert
        assert serializer.data['id'] == employment_entry.id
        assert serializer.data['position_title'] == employment_entry.position_title


class TestEducationEntrySerializer:
    """Tests for EducationEntrySerializer"""

    def test_serialize_education_entry(self, education_entry, db):
        """Test serializing education entry"""
        # Act
        serializer = EducationEntrySerializer(education_entry)
        
        # Assert
        assert serializer.data['id'] == education_entry.id
        assert serializer.data['qualification_name'] == education_entry.qualification_name
        assert serializer.data['institution'] == education_entry.institution


class TestEducationEntryCreationSerializer:
    """Tests for EducationEntryCreationSerializer"""

    def test_serialize_education_entry_creation(self, education_entry, db):
        """Test serializing education entry for creation"""
        # Act
        serializer = EducationEntryCreationSerializer(education_entry)
        
        # Assert
        assert serializer.data['id'] == education_entry.id
        assert serializer.data['qualification_name'] == education_entry.qualification_name


class TestUpdatePISerializer:
    """Tests for UpdatePISerializer"""

    def test_serialize_update_pi(self, user, db):
        """Test serializing personal information update"""
        # Arrange
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'display_first_name': 'Updated',
            'display_last_name': 'Name',
            'email': 'updated@example.com',
        }
        
        # Act
        serializer = UpdatePISerializer(user, data=data, partial=True)
        
        # Assert
        assert serializer.is_valid()
        # Read-only fields (first_name, last_name, email) are not in validated_data
        # Only writable fields are in validated_data
        assert serializer.validated_data['display_first_name'] == 'Updated'
        assert serializer.validated_data['display_last_name'] == 'Name'


class TestUpdateProfileSerializer:
    """Tests for UpdateProfileSerializer"""

    def test_serialize_update_profile(self, user_profile, db):
        """Test serializing profile update"""
        # Arrange
        data = {
            'title': 'prof',
            'middle_initials': 'B',
            'about': 'Updated about',
            'expertise': 'Updated expertise',
        }
        
        # Act
        serializer = UpdateProfileSerializer(user_profile, data=data, partial=True)
        
        # Assert
        assert serializer.is_valid()
        # Read-only field (title) is not in validated_data
        # Only writable fields are in validated_data
        assert serializer.validated_data['about'] == 'Updated about'
        assert serializer.validated_data['expertise'] == 'Updated expertise'


class TestUpdateMembershipSerializer:
    """Tests for UpdateMembershipSerializer"""

    def test_serialize_update_membership(self, user_work, db):
        """Test serializing membership update"""
        # Arrange
        data = {
            'role': 'Updated Role',
        }
        
        # Act
        serializer = UpdateMembershipSerializer(user_work, data=data, partial=True)
        
        # Assert
        assert serializer.is_valid()
        assert serializer.validated_data['role'] == 'Updated Role'


class TestUserWorkAffiliationUpdateSerializer:
    """Tests for UserWorkAffiliationUpdateSerializer"""

    def test_serialize_affiliation_update(self, user_work, db):
        """Test serializing affiliation update"""
        # Arrange
        from agencies.models import Affiliation
        affiliation = Affiliation.objects.create(name='Test Affiliation')
        data = {
            'affiliation': affiliation.id,
        }
        
        # Act
        serializer = UserWorkAffiliationUpdateSerializer(user_work, data=data, partial=True)
        
        # Assert
        assert serializer.is_valid()
        assert serializer.validated_data['affiliation'] == affiliation
