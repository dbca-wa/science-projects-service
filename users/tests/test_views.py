"""
Tests for user views
"""

from rest_framework import status

from common.tests.test_helpers import users_urls


class TestAuthenticationViews:
    """Tests for authentication views"""

    def test_login_success(self, api_client, user, db):
        """Test successful login"""
        # Arrange
        data = {
            "username": "testuser",
            "password": "testpass123",
        }
        user.set_password("testpass123")
        user.save()

        # Act
        response = api_client.post(users_urls.path("log-in"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "ok" in response.data

    def test_login_missing_credentials(self, api_client, db):
        """Test login with missing credentials"""
        # Arrange
        data = {"username": "testuser"}

        # Act
        response = api_client.post(users_urls.path("log-in"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_invalid_credentials(self, api_client, user, db):
        """Test login with invalid credentials"""
        # Arrange
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        user.set_password("testpass123")
        user.save()

        # Act
        response = api_client.post(users_urls.path("log-in"), data, format="json")

        # Assert
        assert "error" in response.data

    def test_logout_authenticated(self, api_client, user, db):
        """Test logout as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.post(users_urls.path("log-out"))

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_logout_unauthenticated(self, api_client, db):
        """Test logout without authentication"""
        # Act
        response = api_client.post(users_urls.path("log-out"))

        # Assert
        # DRF returns 403 when permission class denies access
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_password_success(self, api_client, user, db):
        """Test successful password change"""
        # Arrange
        user.set_password("oldpass123")
        user.save()
        api_client.force_authenticate(user=user)
        data = {
            "old_password": "oldpass123",
            "new_password": "newpass123",
        }

        # Act
        response = api_client.put(
            users_urls.path("change-password"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "ok" in response.data

    def test_change_password_wrong_old_password(self, api_client, user, db):
        """Test password change with wrong old password"""
        # Arrange
        user.set_password("oldpass123")
        user.save()
        api_client.force_authenticate(user=user)
        data = {
            "old_password": "wrongpass",
            "new_password": "newpass123",
        }

        # Act
        response = api_client.put(
            users_urls.path("change-password"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserViews:
    """Tests for user CRUD views"""

    def test_list_users_authenticated(self, api_client, user, user_factory, db):
        """Test listing users as authenticated user"""
        # Arrange
        user_factory.create_batch(3)
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.list())

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "users" in response.data
        assert len(response.data["users"]) > 0

    def test_list_users_unauthenticated(self, api_client, db):
        """Test listing users without authentication"""
        # Act
        response = api_client.get(users_urls.list())

        # Assert
        # DRF returns 403 when permission class denies access
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_with_search(self, api_client, user, user_factory, db):
        """Test listing users with search"""
        # Arrange
        user_factory(username="testuser123")
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.list(), {"search": "test"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "users" in response.data

    def test_create_user(self, api_client, superuser, db):
        """Test creating a user"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
        }

        # Act
        response = api_client.post(users_urls.list(), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newuser"

    def test_get_user_detail(self, api_client, user, db):
        """Test getting user detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.detail(user.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username

    def test_update_user(self, api_client, user, db):
        """Test updating a user"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"first_name": "Updated"}

        # Act
        response = api_client.put(users_urls.detail(user.id), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["first_name"] == "Updated"

    def test_delete_user(self, api_client, superuser, user_factory, db):
        """Test deleting a user"""
        # Arrange
        target_user = user_factory()
        api_client.force_authenticate(user=superuser)

        # Act
        response = api_client.delete(users_urls.detail(target_user.id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestProfileViews:
    """Tests for profile views"""

    def test_list_user_profiles(self, api_client, user, user_profile, db):
        """Test listing user profiles"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("profiles"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_user_profile_detail(self, api_client, user, user_profile, db):
        """Test getting user profile detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("profiles", user_profile.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # ProfilePageSerializer returns nested user object, not just ID
        assert response.data["user"]["id"] == user.id

    def test_update_user_profile(self, api_client, user, user_profile, db):
        """Test updating user profile"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"title": "prof"}

        # Act
        response = api_client.put(
            users_urls.path("profiles", user_profile.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_personal_information(self, api_client, user, db):
        """Test updating personal information"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "first_name": "Updated",
            "last_name": "Name",
        }

        # Act
        response = api_client.put(users_urls.path(user.id, "pi"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_profile(self, api_client, user, user_profile, db):
        """Test updating profile"""
        # Arrange
        api_client.force_authenticate(user=user)
        # UpdateProfile endpoint is for staff_profile fields (about, expertise)
        # title is a UserProfile field, should be updated via /pi endpoint
        # Since user doesn't have staff_profile, this should return 404
        data = {"title": "dr"}

        # Act
        response = api_client.put(
            users_urls.path(user.id, "profile"), data, format="json"
        )

        # Assert
        # User has user_profile but no staff_profile, so should return 404
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStaffProfileViews:
    """Tests for staff profile views"""

    def test_list_staff_profiles(self, api_client, staff_profile, db):
        """Test listing staff profiles"""
        # Act
        response = api_client.get(users_urls.path("staffprofiles"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "profiles" in response.data

    def test_list_staff_profiles_with_search(self, api_client, staff_profile, db):
        """Test listing staff profiles with search"""
        # Act
        response = api_client.get(users_urls.path("staffprofiles"), {"search": "test"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "profiles" in response.data

    def test_create_staff_profile(self, api_client, user, db):
        """Test creating staff profile"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "user": user.id,
            "about": "Test about",
            "expertise": "Test expertise",
        }

        # Act
        response = api_client.post(
            users_urls.path("staffprofiles"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_staff_profile_detail(self, api_client, staff_profile, db):
        """Test getting staff profile detail"""
        # Act
        response = api_client.get(users_urls.path("staffprofiles", staff_profile.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # StaffProfileSerializer returns nested user object, not just ID
        assert response.data["user"]["id"] == staff_profile.user.id

    def test_update_staff_profile(self, api_client, user, staff_profile, db):
        """Test updating staff profile"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"about": "Updated about"}

        # Act
        response = api_client.put(
            users_urls.path("staffprofiles", staff_profile.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_staff_profile(self, api_client, user, staff_profile, db):
        """Test deleting staff profile"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.delete(users_urls.path("staffprofiles", staff_profile.id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_my_staff_profile(self, api_client, user, staff_profile, db):
        """Test getting current user's staff profile"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("mypublicprofile"))

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_toggle_public_visibility(self, api_client, user, staff_profile, db):
        """Test toggling staff profile visibility"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.post(
            users_urls.path("staffprofiles", staff_profile.id, "toggle_visibility")
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_get_active_staff_emails(self, api_client, user, staff_profile, db):
        """Test getting active staff emails"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("get_staff_profile_emails"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestProfileEntryViews:
    """Tests for profile entry views"""

    def test_employment_entries_url_matches_view_signature(
        self, api_client, staff_profile, user, db
    ):
        """Test that employment entries URL correctly captures profile_id parameter"""
        # This test verifies there is NO production bug - the URL pattern DOES capture profile_id
        # URL: path("profiles/<int:profile_id>/employment_entries", ...)
        # View: def get(self, request, profile_id):
        # They match correctly!

        # Arrange - Login as the user who owns the profile
        api_client.force_authenticate(user=staff_profile.user)

        # Act - Call the endpoint
        response = api_client.get(
            users_urls.path("profiles", staff_profile.id, "employment_entries")
        )

        # Assert - Should get 200 OK (not 404 which would indicate URL mismatch)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_education_entries_url_matches_view_signature(
        self, api_client, staff_profile, user, db
    ):
        """Test that education entries URL correctly captures profile_id parameter"""
        # This test verifies there is NO production bug - the URL pattern DOES capture profile_id
        # URL: path("profiles/<int:profile_id>/education_entries", ...)
        # View: def get(self, request, profile_id):
        # They match correctly!

        # Arrange - Login as the user who owns the profile
        api_client.force_authenticate(user=staff_profile.user)

        # Act - Call the endpoint
        response = api_client.get(
            users_urls.path("profiles", staff_profile.id, "education_entries")
        )

        # Assert - Should get 200 OK (not 404 which would indicate URL mismatch)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestProfileSectionViews:
    """Tests for profile section views"""

    def test_get_staff_profile_hero(self, api_client, staff_profile, db):
        """Test getting staff profile hero section"""
        # Act
        response = api_client.get(
            users_urls.path("staffprofiles", staff_profile.id, "hero")
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data

    def test_get_staff_profile_overview(self, api_client, staff_profile, db):
        """Test getting staff profile overview section"""
        # Act
        response = api_client.get(
            users_urls.path("staffprofiles", staff_profile.id, "overview")
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "expertise" in response.data

    def test_get_staff_profile_cv(self, api_client, staff_profile, db):
        """Test getting staff profile CV section"""
        # Act
        response = api_client.get(
            users_urls.path("staffprofiles", staff_profile.id, "cv")
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "employment_entries" in response.data
        assert "education_entries" in response.data


class TestAdminViews:
    """Tests for admin operation views"""

    def test_toggle_user_active(self, api_client, superuser, user_factory, db):
        """Test toggling user active status"""
        # Arrange
        target_user = user_factory(is_active=True)
        api_client.force_authenticate(user=superuser)

        # Act
        response = api_client.post(users_urls.path(target_user.id, "toggleactive"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_toggle_user_active_requires_admin(
        self, api_client, user, user_factory, db
    ):
        """Test toggling user active requires admin permission"""
        # Arrange
        target_user = user_factory()
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.post(users_urls.path(target_user.id, "toggleactive"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_switch_admin(self, api_client, superuser, user_factory, db):
        """Test toggling user admin status"""
        # Arrange
        target_user = user_factory(is_superuser=False)
        api_client.force_authenticate(user=superuser)

        # Act
        response = api_client.post(users_urls.path(target_user.id, "admin"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_superuser"] is True

    def test_switch_admin_requires_admin(self, api_client, user, user_factory, db):
        """Test switching admin requires admin permission"""
        # Arrange
        target_user = user_factory()
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.post(users_urls.path(target_user.id, "admin"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUtilityViews:
    """Tests for utility views"""

    def test_check_email_exists_true(self, api_client, user, db):
        """Test checking if email exists - returns true"""
        # Act
        response = api_client.get(
            users_urls.path("check-email-exists"), {"email": user.email}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["exists"] is True

    def test_check_email_exists_false(self, api_client, db):
        """Test checking if email exists - returns false"""
        # Act
        response = api_client.get(
            users_urls.path("check-email-exists"), {"email": "nonexistent@example.com"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["exists"] is False

    def test_check_email_exists_missing_param(self, api_client, db):
        """Test checking email without email parameter"""
        # Act
        response = api_client.get(users_urls.path("check-email-exists"))

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_check_name_exists_true(self, api_client, user, db):
        """Test checking if username exists - returns true"""
        # Act
        response = api_client.get(
            users_urls.path("check-name-exists"), {"username": user.username}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["exists"] is True

    def test_check_name_exists_false(self, api_client, db):
        """Test checking if username exists - returns false"""
        # Act
        response = api_client.get(
            users_urls.path("check-name-exists"), {"username": "nonexistent"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["exists"] is False

    def test_check_name_exists_missing_param(self, api_client, db):
        """Test checking username without username parameter"""
        # Act
        response = api_client.get(users_urls.path("check-name-exists"))

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_check_user_is_staff_true(self, api_client, user, staff_user, db):
        """Test checking if user is staff - returns true"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            users_urls.path("is_staff", staff_user.id), {"user_id": staff_user.id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_staff"] is True

    def test_check_user_is_staff_false(self, api_client, user, user_factory, db):
        """Test checking if user is staff - returns false"""
        # Arrange
        regular_user = user_factory(is_staff=False)
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            users_urls.path("is_staff", regular_user.id), {"user_id": regular_user.id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_staff"] is False

    def test_check_user_is_staff_missing_param(self, api_client, user, db):
        """Test checking staff status without user_id parameter"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("is_staff", 999))

        # Assert - Should return 400 for missing user_id query param
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_me_authenticated(self, api_client, user, db):
        """Test getting current user info"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("me"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.id
        assert response.data["username"] == user.username

    def test_me_unauthenticated(self, api_client, db):
        """Test getting current user without authentication"""
        # Act
        response = api_client.get(users_urls.path("me"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_small_internal_user_search(self, api_client, user, user_factory, db):
        """Test searching users"""
        # Arrange
        user_factory(username="searchuser1", first_name="Search", last_name="User1")
        user_factory(username="searchuser2", first_name="Search", last_name="User2")
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("smallsearch"), {"search": "search"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 2

    def test_small_internal_user_search_short_query(self, api_client, user, db):
        """Test searching users with short query returns empty"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("smallsearch"), {"search": "a"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


class TestStaffProfileAdvancedViews:
    """Tests for advanced staff profile views"""

    def test_list_staff_profiles_with_filters(
        self, api_client, staff_profile, business_area, db
    ):
        """Test listing staff profiles with filters"""
        # Arrange
        staff_profile.user.business_area = business_area
        staff_profile.user.save()

        # Act
        response = api_client.get(
            users_urls.path("staffprofiles"),
            {
                "business_area": business_area.id,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "profiles" in response.data

    def test_check_staff_profile_exists_true(self, api_client, user, staff_profile, db):
        """Test checking if staff profile exists - returns true"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            users_urls.path(user.id, "check_staff_profile"), {"user_id": user.id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["exists"] is True
        assert "profile" in response.data

    def test_check_staff_profile_exists_false(self, api_client, user, user_factory, db):
        """Test checking if staff profile exists - returns false"""
        # Arrange
        other_user = user_factory()
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            users_urls.path(user.id, "check_staff_profile"), {"user_id": other_user.id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["exists"] is False
        assert response.data["profile"] is None

    def test_check_staff_profile_missing_param(self, api_client, user, db):
        """Test checking staff profile without user_id parameter"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path(user.id, "check_staff_profile"))

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_download_bcs_staff_csv(self, api_client, user, staff_profile, db):
        """Test downloading staff profiles as CSV"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("download_bcs_csv"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_staff_profile_projects(self, api_client, user, staff_profile, db):
        """Test getting staff profile projects"""
        # Arrange - Create a project membership
        from common.tests.factories import ProjectFactory
        from projects.models import ProjectMember

        project = ProjectFactory()
        ProjectMember.objects.create(
            project=project,
            user=user,
            role="Test Role",
        )

        # Act
        response = api_client.get(users_urls.path(user.id, "projects_staff_profile"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_staff_profile_projects_no_memberships(self, api_client, user_factory, db):
        """Test getting staff profile projects with no memberships"""
        # Arrange
        user = user_factory()

        # Act
        response = api_client.get(users_urls.path(user.id, "projects_staff_profile"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_public_email_staff_member_dev_mode(
        self, api_client, staff_profile, db, settings
    ):
        """Test sending public email to staff member in dev mode"""
        # Arrange
        settings.ENVIRONMENT = "development"
        data = {
            "senderEmail": "sender@example.com",
            "message": "Test message",
        }

        # Act
        response = api_client.post(
            users_urls.path(staff_profile.user.id, "public_email_staff_member"),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "ok" in response.data

    def test_public_email_staff_member_not_found(self, api_client, db):
        """Test sending email to non-existent staff profile"""
        # Arrange
        data = {
            "senderEmail": "sender@example.com",
            "message": "Test message",
        }

        # Act
        response = api_client.post(
            users_urls.path(999, "public_email_staff_member"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserProfileAdvancedViews:
    """Tests for advanced user profile views"""

    def test_list_user_profiles_with_filter(self, api_client, user, user_profile, db):
        """Test listing user profiles with user filter"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("profiles"), {"user": user.id})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_update_membership(self, api_client, user, user_work, db):
        """Test updating user membership"""
        # Arrange
        api_client.force_authenticate(user=user)
        user.work = user_work
        user.save()
        data = {"role": "Updated Role"}

        # Act
        response = api_client.put(
            users_urls.path(user.id, "membership"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["role"] == "Updated Role"

    def test_update_membership_no_work(self, api_client, user, db):
        """Test updating membership when user has no work record"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"role": "Updated Role"}

        # Act
        response = api_client.put(
            users_urls.path(user.id, "membership"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data

    def test_remove_avatar_no_avatar(self, api_client, user, db):
        """Test removing avatar when user has no avatar"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.delete(users_urls.path(user.id, "remove_avatar"))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_user_works(self, api_client, user, user_work, db):
        """Test listing all user works"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(users_urls.path("work"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_create_user_work(self, api_client, user, user_factory, business_area, db):
        """Test creating user work"""
        # Arrange
        target_user = user_factory()
        api_client.force_authenticate(user=user)
        data = {
            "user": target_user.id,
            "business_area": business_area.id,
            "role": "Test Role",
        }

        # Act
        response = api_client.post(users_urls.path("work"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_user_work(self, api_client, user, user_work, db):
        """Test updating user work"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"role": "Updated Role"}

        # Act
        response = api_client.put(
            users_urls.path("work", user_work.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_users_projects(self, api_client, user, db):
        """Test getting user's projects"""
        # Arrange - Create a project membership
        from common.tests.factories import ProjectFactory
        from projects.models import ProjectMember

        project = ProjectFactory()
        ProjectMember.objects.create(
            project=project,
            user=user,
            role="Test Role",
        )

        # Act
        response = api_client.get(users_urls.path(user.id, "projects"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_users_projects_no_memberships(self, api_client, user_factory, db):
        """Test getting user's projects with no memberships"""
        # Arrange
        user = user_factory()

        # Act
        response = api_client.get(users_urls.path(user.id, "projects"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_update_profile_user_not_found(self, api_client, user, db):
        """Test updating profile for non-existent user"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"title": "dr"}

        # Act
        response = api_client.put(users_urls.path(999, "profile"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_profile_user_no_profile(self, api_client, user, user_factory, db):
        """Test updating profile for user without profile"""
        # Arrange
        target_user = user_factory()
        api_client.force_authenticate(user=user)
        data = {"title": "dr"}

        # Act
        response = api_client.put(
            users_urls.path(target_user.id, "profile"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
