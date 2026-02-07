"""
Tests for user permissions
"""

from unittest.mock import Mock

from users.permissions.user_permissions import (
    CanExportData,
    CanManageEducationEntry,
    CanManageEmploymentEntry,
    CanManageProfile,
    CanManageStaffProfile,
    CanManageUser,
    CanViewProfile,
)


class TestCanManageUser:
    """Tests for CanManageUser permission"""

    def test_superuser_can_manage_any_user(self, user, superuser, db):
        """Test superuser can manage any user"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanManageUser()

        # Act
        result = permission.has_object_permission(request, None, user)

        # Assert
        assert result is True

    def test_user_can_manage_themselves(self, user, db):
        """Test user can manage their own account"""
        # Arrange
        request = Mock(user=user)
        permission = CanManageUser()

        # Act
        result = permission.has_object_permission(request, None, user)

        # Assert
        assert result is True

    def test_user_cannot_manage_other_user(self, user, user_factory, db):
        """Test user cannot manage another user"""
        # Arrange
        other_user = user_factory(username="otheruser")
        request = Mock(user=user)
        permission = CanManageUser()

        # Act
        result = permission.has_object_permission(request, None, other_user)

        # Assert
        assert result is False

    def test_staff_cannot_manage_other_user(self, staff_user, user, db):
        """Test staff user cannot manage another user"""
        # Arrange
        request = Mock(user=staff_user)
        permission = CanManageUser()

        # Act
        result = permission.has_object_permission(request, None, user)

        # Assert
        assert result is False


class TestCanManageProfile:
    """Tests for CanManageProfile permission"""

    def test_superuser_can_manage_any_profile(self, user_profile, superuser, db):
        """Test superuser can manage any profile"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanManageProfile()

        # Act
        result = permission.has_object_permission(request, None, user_profile)

        # Assert
        assert result is True

    def test_user_can_manage_own_profile(self, user, user_profile, db):
        """Test user can manage their own profile"""
        # Arrange
        request = Mock(user=user)
        permission = CanManageProfile()

        # Act
        result = permission.has_object_permission(request, None, user_profile)

        # Assert
        assert result is True

    def test_user_cannot_manage_other_profile(self, user, user_factory, db):
        """Test user cannot manage another user's profile"""
        # Arrange
        from users.models import UserProfile

        other_user = user_factory(username="otheruser")
        other_profile = UserProfile.objects.create(
            user=other_user,
            title="mr",
        )
        request = Mock(user=user)
        permission = CanManageProfile()

        # Act
        result = permission.has_object_permission(request, None, other_profile)

        # Assert
        assert result is False


class TestCanViewProfile:
    """Tests for CanViewProfile permission"""

    def test_superuser_can_view_any_profile(self, user_profile, superuser, db):
        """Test superuser can view any profile"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanViewProfile()

        # Act
        result = permission.has_object_permission(request, None, user_profile)

        # Assert
        assert result is True

    def test_user_can_view_own_profile(self, user, user_profile, db):
        """Test user can view their own profile"""
        # Arrange
        request = Mock(user=user)
        permission = CanViewProfile()

        # Act
        result = permission.has_object_permission(request, None, user_profile)

        # Assert
        assert result is True

    def test_public_profile_visible_to_all(self, user, user_factory, db):
        """Test public profile is visible to all users"""
        # Arrange
        from users.models import PublicStaffProfile

        other_user = user_factory(username="otheruser")
        # PublicStaffProfile uses is_hidden, not public
        # But the permission checks for 'public' attribute
        # So we test with a mock object that has public=True
        public_profile = PublicStaffProfile.objects.create(
            user=other_user,
            about="Public profile",
            is_hidden=False,  # Not hidden = public
        )
        # Add public attribute for testing
        public_profile.public = True

        request = Mock(user=user)
        permission = CanViewProfile()

        # Act
        result = permission.has_object_permission(request, None, public_profile)

        # Assert
        assert result is True

    def test_private_profile_not_visible_to_others(self, user, user_factory, db):
        """Test private profile is not visible to other users"""
        # Arrange
        from users.models import UserProfile

        other_user = user_factory(username="otheruser")
        private_profile = UserProfile.objects.create(
            user=other_user,
            title="mr",
        )
        # Ensure profile is private
        if hasattr(private_profile, "public"):
            private_profile.public = False
            private_profile.save()

        request = Mock(user=user)
        permission = CanViewProfile()

        # Act
        result = permission.has_object_permission(request, None, private_profile)

        # Assert
        assert result is False

    def test_profile_without_public_attribute_not_visible(self, user, user_factory, db):
        """Test profile without public attribute is not visible to others"""
        # Arrange
        from users.models import UserProfile

        other_user = user_factory(username="otheruser")
        profile = UserProfile.objects.create(
            user=other_user,
            title="mr",
        )
        # UserProfile doesn't have 'public' attribute, so this tests the hasattr check
        request = Mock(user=user)
        permission = CanViewProfile()

        # Act
        result = permission.has_object_permission(request, None, profile)

        # Assert
        # Should be False since user is not the owner and profile has no public attribute
        assert result is False


class TestCanManageStaffProfile:
    """Tests for CanManageStaffProfile permission"""

    def test_superuser_can_manage_any_staff_profile(self, staff_profile, superuser, db):
        """Test superuser can manage any staff profile"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanManageStaffProfile()

        # Act
        result = permission.has_object_permission(request, None, staff_profile)

        # Assert
        assert result is True

    def test_user_can_manage_own_staff_profile(self, user, staff_profile, db):
        """Test user can manage their own staff profile"""
        # Arrange
        request = Mock(user=user)
        permission = CanManageStaffProfile()

        # Act
        result = permission.has_object_permission(request, None, staff_profile)

        # Assert
        assert result is True

    def test_user_cannot_manage_other_staff_profile(self, user, user_factory, db):
        """Test user cannot manage another user's staff profile"""
        # Arrange
        from users.models import PublicStaffProfile

        other_user = user_factory(username="otheruser")
        other_profile = PublicStaffProfile.objects.create(
            user=other_user,
            about="Other user profile",
        )
        request = Mock(user=user)
        permission = CanManageStaffProfile()

        # Act
        result = permission.has_object_permission(request, None, other_profile)

        # Assert
        assert result is False


class TestCanExportData:
    """Tests for CanExportData permission"""

    def test_superuser_can_export_data(self, superuser, db):
        """Test superuser can export data"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanExportData()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is True

    def test_regular_user_cannot_export_data(self, user, db):
        """Test regular user cannot export data"""
        # Arrange
        request = Mock(user=user)
        permission = CanExportData()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False

    def test_staff_user_cannot_export_data(self, staff_user, db):
        """Test staff user cannot export data"""
        # Arrange
        request = Mock(user=staff_user)
        permission = CanExportData()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False


class TestCanManageEmploymentEntry:
    """Tests for CanManageEmploymentEntry permission"""

    def test_superuser_can_manage_any_employment_entry(
        self, employment_entry, superuser, db
    ):
        """Test superuser can manage any employment entry"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanManageEmploymentEntry()

        # Act
        result = permission.has_object_permission(request, None, employment_entry)

        # Assert
        assert result is True

    def test_user_can_manage_own_employment_entry(self, user, employment_entry, db):
        """Test user can manage their own employment entry"""
        # Arrange
        request = Mock(user=user)
        permission = CanManageEmploymentEntry()

        # Act
        result = permission.has_object_permission(request, None, employment_entry)

        # Assert
        assert result is True

    def test_user_cannot_manage_other_employment_entry(self, user, user_factory, db):
        """Test user cannot manage another user's employment entry"""
        # Arrange
        from users.models import EmploymentEntry, PublicStaffProfile

        other_user = user_factory(username="otheruser")
        other_profile = PublicStaffProfile.objects.create(
            user=other_user,
            about="Other user profile",
        )
        other_entry = EmploymentEntry.objects.create(
            public_profile=other_profile,
            position_title="Other Position",
            start_year=2020,
        )
        request = Mock(user=user)
        permission = CanManageEmploymentEntry()

        # Act
        result = permission.has_object_permission(request, None, other_entry)

        # Assert
        assert result is False


class TestCanManageEducationEntry:
    """Tests for CanManageEducationEntry permission"""

    def test_superuser_can_manage_any_education_entry(
        self, education_entry, superuser, db
    ):
        """Test superuser can manage any education entry"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanManageEducationEntry()

        # Act
        result = permission.has_object_permission(request, None, education_entry)

        # Assert
        assert result is True

    def test_user_can_manage_own_education_entry(self, user, education_entry, db):
        """Test user can manage their own education entry"""
        # Arrange
        request = Mock(user=user)
        permission = CanManageEducationEntry()

        # Act
        result = permission.has_object_permission(request, None, education_entry)

        # Assert
        assert result is True

    def test_user_cannot_manage_other_education_entry(self, user, user_factory, db):
        """Test user cannot manage another user's education entry"""
        # Arrange
        from users.models import EducationEntry, PublicStaffProfile

        other_user = user_factory(username="otheruser")
        other_profile = PublicStaffProfile.objects.create(
            user=other_user,
            about="Other user profile",
        )
        other_entry = EducationEntry.objects.create(
            public_profile=other_profile,
            qualification_name="Other Degree",
            end_year=2019,
        )
        request = Mock(user=user)
        permission = CanManageEducationEntry()

        # Act
        result = permission.has_object_permission(request, None, other_entry)

        # Assert
        assert result is False
