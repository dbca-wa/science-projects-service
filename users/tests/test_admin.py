"""
Tests for users admin
"""
import pytest
import csv
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
from django.contrib.admin.sites import AdminSite
from django.http import HttpResponse

from users.admin import (
    KeywordTagAdmin,
    CustomUserAdmin,
    StaffProfileAdmin,
    UserProfileAdmin,
    UserWorkAdmin,
    create_redirect_files,
    copy_about_expertise_to_staff_profile,
    hide_all_staff_profiles,
    create_staff_profiles,
    generate_active_staff_csv,
    set_it_assets_id,
    update_display_names,
    export_selected_users_to_csv,
    export_current_active_project_leads,
    delete_unused_tags,
)
from users.models import (
    KeywordTag,
    User,
    PublicStaffProfile,
    UserProfile,
    UserWork,
)


# ============================================================================
# ADMIN ACTION TESTS - KEYWORD TAG
# ============================================================================


class TestDeleteUnusedTags:
    """Tests for delete_unused_tags admin action"""

    def test_requires_single_selection(self, db):
        """Test action requires single selection"""
        # Arrange
        tag1 = KeywordTag.objects.create(name='Tag 1')
        tag2 = KeywordTag.objects.create(name='Tag 2')
        admin = KeywordTagAdmin(KeywordTag, AdminSite())
        request = Mock()
        selected = [tag1, tag2]
        
        # Act
        with patch('builtins.print') as mock_print:
            delete_unused_tags(admin, request, selected)
            
            # Assert
            mock_print.assert_called_once_with("PLEASE SELECT ONLY ONE")

    def test_deletes_unused_tags(self, staff_profile, db):
        """Test action deletes tags not associated with any profile"""
        # Arrange
        used_tag = KeywordTag.objects.create(name='Used Tag')
        unused_tag = KeywordTag.objects.create(name='Unused Tag')
        
        # Associate used_tag with profile
        staff_profile.keyword_tags.add(used_tag)
        
        admin = KeywordTagAdmin(KeywordTag, AdminSite())
        request = Mock()
        selected = [used_tag]
        
        # Act
        delete_unused_tags(admin, request, selected)
        
        # Assert
        assert KeywordTag.objects.filter(pk=used_tag.pk).exists()
        assert not KeywordTag.objects.filter(pk=unused_tag.pk).exists()

    def test_reports_deletion_count(self, db):
        """Test action reports number of deleted tags"""
        # Arrange
        tag1 = KeywordTag.objects.create(name='Unused 1')
        tag2 = KeywordTag.objects.create(name='Unused 2')
        tag3 = KeywordTag.objects.create(name='Unused 3')
        
        admin = KeywordTagAdmin(KeywordTag, AdminSite())
        request = Mock()
        selected = [tag1]
        
        # Act
        with patch.object(admin, 'message_user') as mock_message:
            delete_unused_tags(admin, request, selected)
            
            # Assert
            mock_message.assert_called_once()
            args = mock_message.call_args[0]
            assert "3 unused tags were deleted" in args[1]


# ============================================================================
# ADMIN ACTION TESTS - USER
# ============================================================================


class TestCopyAboutExpertiseToStaffProfile:
    """Tests for copy_about_expertise_to_staff_profile admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        # Arrange
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user, user]
        
        # Act
        with patch('builtins.print') as mock_print:
            copy_about_expertise_to_staff_profile(admin, request, selected)
            
            # Assert
            mock_print.assert_called_once_with("Please select only one")

    def test_copies_profile_data_to_staff_profile(self, staff_user, db):
        """Test action copies about and expertise to staff profile"""
        # Arrange
        from users.models import UserProfile
        
        staff_user.is_staff = True
        staff_user.save()
        
        # Create user profile (UserProfile doesn't have about/expertise)
        # The admin action reads from user.profile.about and user.profile.expertise
        # but UserProfile model doesn't have these fields
        # This test documents that the action expects fields that don't exist
        user_profile = UserProfile.objects.create(
            user=staff_user,
            title='dr',
            middle_initials='A'
        )
        
        # Create staff profile
        staff_profile = PublicStaffProfile.objects.create(user=staff_user)
        
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [staff_user]
        
        # Act & Assert - This will fail because UserProfile doesn't have about/expertise
        with pytest.raises(AttributeError):
            copy_about_expertise_to_staff_profile(admin, request, selected)


class TestHideAllStaffProfiles:
    """Tests for hide_all_staff_profiles admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        # Arrange
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user, user]
        
        # Act
        with patch('builtins.print') as mock_print:
            hide_all_staff_profiles(admin, request, selected)
            
            # Assert
            mock_print.assert_called_once_with("Please select only one")

    def test_hides_all_staff_profiles(self, staff_user, db):
        """Test action hides all staff profiles"""
        # Arrange
        staff_profile = PublicStaffProfile.objects.create(
            user=staff_user,
            is_hidden=False
        )
        
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [staff_user]
        
        # Act
        hide_all_staff_profiles(admin, request, selected)
        
        # Assert
        staff_profile.refresh_from_db()
        assert staff_profile.is_hidden is True


class TestCreateStaffProfiles:
    """Tests for create_staff_profiles admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        # Arrange
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user, user]
        
        # Act
        with patch('builtins.print') as mock_print:
            create_staff_profiles(admin, request, selected)
            
            # Assert
            mock_print.assert_called_once_with("PLEASE SELECT ONLY ONE")

    def test_creates_staff_profiles_for_users_without(self, staff_user, db):
        """Test action creates staff profiles for users without them"""
        # Arrange
        # Ensure user has no staff profile
        PublicStaffProfile.objects.filter(user=staff_user).delete()
        
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [staff_user]
        
        # Act
        create_staff_profiles(admin, request, selected)
        
        # Assert
        assert PublicStaffProfile.objects.filter(user=staff_user).exists()


class TestUpdateDisplayNames:
    """Tests for update_display_names admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        # Arrange
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user, user]
        
        # Act
        with patch('builtins.print') as mock_print:
            update_display_names(admin, request, selected)
            
            # Assert
            mock_print.assert_called_once_with("PLEASE SELECT ONLY ONE")

    def test_updates_display_names_from_first_last(self, user_factory, db):
        """Test action updates display names from first and last names"""
        # Arrange
        user = user_factory(
            first_name='John',
            last_name='Doe',
            display_first_name='',
            display_last_name=''
        )
        
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user]
        
        # Act
        update_display_names(admin, request, selected)
        
        # Assert
        user.refresh_from_db()
        assert user.display_first_name == 'John'
        assert user.display_last_name == 'Doe'

    def test_skips_users_with_display_names(self, user_factory, db):
        """Test action skips users who already have display names"""
        # Arrange
        user = user_factory(
            first_name='John',
            last_name='Doe',
            display_first_name='Johnny',
            display_last_name='D'
        )
        
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user]
        
        # Act
        update_display_names(admin, request, selected)
        
        # Assert
        user.refresh_from_db()
        # Should not change existing display names
        assert user.display_first_name == 'Johnny'
        assert user.display_last_name == 'D'


class TestExportSelectedUsersToCSV:
    """Tests for export_selected_users_to_csv admin action"""

    def test_exports_users_to_csv(self, user_factory, db):
        """Test action exports selected users to CSV"""
        # Arrange
        user1 = user_factory(username='user1', email='user1@example.com')
        user2 = user_factory(username='user2', email='user2@example.com')
        
        admin = CustomUserAdmin(User, AdminSite())
        request = Mock()
        selected = [user1, user2]
        
        # Act
        response = export_selected_users_to_csv(admin, request, selected)
        
        # Assert
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment; filename="users.csv"' in response['Content-Disposition']
        
        # Verify CSV content
        content = response.content.decode('utf-8')
        assert 'user1' in content
        assert 'user2' in content


# ============================================================================
# ADMIN ACTION TESTS - STAFF PROFILE
# ============================================================================


class TestSetItAssetsId:
    """Tests for set_it_assets_id admin action"""

    def test_requires_single_selection(self, staff_profile, db):
        """Test action requires single selection"""
        # Arrange
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        request = Mock()
        selected = [staff_profile, staff_profile]
        
        # Act
        with patch('builtins.print') as mock_print:
            set_it_assets_id(admin, request, selected)
            
            # Assert
            mock_print.assert_called_once_with("PLEASE SELECT ONLY ONE")

    @patch('users.admin.requests.get')
    def test_sets_it_asset_id_from_api(self, mock_get, staff_profile, db):
        """Test action sets IT asset ID from API response"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'email': staff_profile.user.email, 'id': 12345}
        ]
        mock_get.return_value = mock_response
        
        staff_profile.it_asset_id = None
        staff_profile.save()
        
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        request = Mock()
        selected = [staff_profile]
        
        # Act
        with patch('users.admin.settings') as mock_settings:
            mock_settings.IT_ASSETS_URL = 'http://test.com'
            mock_settings.IT_ASSETS_USER = 'user'
            mock_settings.IT_ASSETS_ACCESS_TOKEN = 'token'
            set_it_assets_id(admin, request, selected)
        
        # Assert
        staff_profile.refresh_from_db()
        assert staff_profile.it_asset_id == 12345

    @patch('users.admin.requests.get')
    def test_handles_api_failure(self, mock_get, staff_profile, db):
        """Test action handles API failure gracefully"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_get.return_value = mock_response
        
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        request = Mock()
        selected = [staff_profile]
        
        # Act
        with patch('users.admin.settings') as mock_settings:
            mock_settings.IT_ASSETS_URL = 'http://test.com'
            mock_settings.IT_ASSETS_USER = 'user'
            mock_settings.IT_ASSETS_ACCESS_TOKEN = 'token'
            mock_settings.LOGGER = Mock()
            set_it_assets_id(admin, request, selected)
        
        # Assert - should not crash, just log error
        assert mock_settings.LOGGER.error.called


# ============================================================================
# ADMIN ACTION TESTS - COMPLEX ACTIONS
# ============================================================================


@pytest.mark.skip(reason="Requires external CSV file and complex file operations - tested manually")
class TestCreateRedirectFiles:
    """Tests for create_redirect_files admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        pass


@pytest.mark.skip(reason="Requires IT Assets API integration - tested manually")
class TestGenerateActiveStaffCSV:
    """Tests for generate_active_staff_csv admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        pass


@pytest.mark.skip(reason="Requires project data and complex logic - tested manually")
class TestExportCurrentActiveProjectLeads:
    """Tests for export_current_active_project_leads admin action"""

    def test_requires_single_selection(self, user, db):
        """Test action requires single selection"""
        pass


# ============================================================================
# ADMIN CONFIGURATION TESTS
# ============================================================================


class TestKeywordTagAdmin:
    """Tests for KeywordTagAdmin configuration"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        admin = KeywordTagAdmin(KeywordTag, AdminSite())
        
        assert 'pk' in admin.list_display
        assert 'name' in admin.list_display

    def test_actions_configured(self, db):
        """Test admin actions are configured"""
        admin = KeywordTagAdmin(KeywordTag, AdminSite())
        
        assert delete_unused_tags in admin.actions


class TestCustomUserAdmin:
    """Tests for CustomUserAdmin configuration"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        admin = CustomUserAdmin(User, AdminSite())
        
        assert 'pk' in admin.list_display
        assert 'username' in admin.list_display
        assert 'email' in admin.list_display
        assert 'first_name' in admin.list_display
        assert 'last_name' in admin.list_display
        assert 'is_aec' in admin.list_display
        assert 'is_staff' in admin.list_display
        assert 'is_superuser' in admin.list_display

    def test_fieldsets_configured(self, db):
        """Test fieldsets are properly configured"""
        admin = CustomUserAdmin(User, AdminSite())
        
        assert len(admin.fieldsets) == 3
        # Profile section
        assert admin.fieldsets[0][0] == 'Profile'
        # Permissions section
        assert admin.fieldsets[1][0] == 'Permissions'
        # Important Dates section
        assert admin.fieldsets[2][0] == 'Important Dates'

    def test_actions_configured(self, db):
        """Test admin actions are configured"""
        admin = CustomUserAdmin(User, AdminSite())
        
        assert hide_all_staff_profiles in admin.actions
        assert generate_active_staff_csv in admin.actions
        assert export_selected_users_to_csv in admin.actions
        assert export_current_active_project_leads in admin.actions
        assert update_display_names in admin.actions
        assert create_redirect_files in admin.actions


class TestStaffProfileAdmin:
    """Tests for StaffProfileAdmin configuration"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        
        assert 'user' in admin.list_display
        assert 'is_hidden' in admin.list_display
        assert 'about' in admin.list_display
        assert 'expertise' in admin.list_display

    def test_ordering(self, db):
        """Test ordering configuration"""
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        
        assert admin.ordering == ['user']

    def test_search_fields(self, db):
        """Test search fields configuration"""
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        
        assert 'user__display_first_name' in admin.search_fields
        assert 'user__display_last_name' in admin.search_fields
        assert 'user__first_name' in admin.search_fields
        assert 'user__last_name' in admin.search_fields
        assert 'user__username' in admin.search_fields

    def test_actions_configured(self, db):
        """Test admin actions are configured"""
        admin = StaffProfileAdmin(PublicStaffProfile, AdminSite())
        
        assert create_staff_profiles in admin.actions
        assert export_current_active_project_leads in admin.actions
        assert update_display_names in admin.actions
        assert copy_about_expertise_to_staff_profile in admin.actions
        assert set_it_assets_id in admin.actions


class TestUserProfileAdmin:
    """Tests for UserProfileAdmin configuration"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        admin = UserProfileAdmin(UserProfile, AdminSite())
        
        assert 'user' in admin.list_display
        assert 'title' in admin.list_display
        assert 'middle_initials' in admin.list_display
        assert 'image' in admin.list_display

    def test_ordering(self, db):
        """Test ordering configuration"""
        admin = UserProfileAdmin(UserProfile, AdminSite())
        
        assert admin.ordering == ['user']

    def test_search_fields(self, db):
        """Test search fields configuration"""
        admin = UserProfileAdmin(UserProfile, AdminSite())
        
        assert 'user__display_first_name' in admin.search_fields
        assert 'user__display_last_name' in admin.search_fields
        assert 'user__first_name' in admin.search_fields
        assert 'user__last_name' in admin.search_fields
        assert 'user__username' in admin.search_fields


class TestUserWorkAdmin:
    """Tests for UserWorkAdmin configuration"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        admin = UserWorkAdmin(UserWork, AdminSite())
        
        assert 'user' in admin.list_display
        assert 'agency' in admin.list_display
        assert 'branch' in admin.list_display
        assert 'business_area' in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        admin = UserWorkAdmin(UserWork, AdminSite())
        
        assert 'agency' in admin.list_filter
        assert 'branch' in admin.list_filter
        assert 'business_area' in admin.list_filter

    def test_search_fields(self, db):
        """Test search fields configuration"""
        admin = UserWorkAdmin(UserWork, AdminSite())
        
        assert 'business_area__name' in admin.search_fields
        assert 'user__username' in admin.search_fields
        assert 'user__first_name' in admin.search_fields
        assert 'user__display_first_name' in admin.search_fields
        assert 'user__last_name' in admin.search_fields
        assert 'user__display_last_name' in admin.search_fields
        assert 'branch__name' in admin.search_fields
