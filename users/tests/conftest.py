"""
User-specific pytest fixtures.

Provides fixtures for testing user-related functionality.
"""

import pytest
from django.contrib.auth import get_user_model

from common.tests.factories import BusinessAreaFactory, UserFactory

User = get_user_model()


@pytest.fixture
def user(db):
    """
    Provide a regular user.

    Returns:
        User: User instance
    """
    return UserFactory(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def superuser(db):
    """
    Provide a superuser.

    Returns:
        User: Superuser instance
    """
    return UserFactory(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def staff_user(db):
    """
    Provide a staff user.

    Returns:
        User: Staff user instance
    """
    return UserFactory(
        username="staffuser",
        email="staff@example.com",
        first_name="Staff",
        last_name="User",
        is_staff=True,
    )


@pytest.fixture
def business_area(db):
    """
    Provide a business area.

    Returns:
        BusinessArea: Business area instance
    """
    return BusinessAreaFactory()


@pytest.fixture
def user_profile(db, user):
    """
    Provide a user profile.

    Args:
        user: User fixture

    Returns:
        UserProfile: User profile instance
    """
    from users.models import UserProfile

    return UserProfile.objects.create(
        user=user,
        title="dr",
        middle_initials="A",
    )


@pytest.fixture
def staff_profile(db, user):
    """
    Provide a public staff profile.

    Args:
        user: User fixture

    Returns:
        PublicStaffProfile: Staff profile instance
    """
    from users.models import PublicStaffProfile

    return PublicStaffProfile.objects.create(
        user=user,
        about="Test about text",
        expertise="Test expertise",
        public_email="public@example.com",
        public_email_on=True,
        custom_title="Test Title",
        custom_title_on=True,
    )


@pytest.fixture
def employment_entry(db, staff_profile):
    """
    Provide an employment entry.

    Args:
        staff_profile: Staff profile fixture

    Returns:
        EmploymentEntry: Employment entry instance
    """
    from users.models import EmploymentEntry

    return EmploymentEntry.objects.create(
        public_profile=staff_profile,
        position_title="Test Position",
        start_year=2020,
        end_year=2023,
        section="Test Section",
        employer="Test Employer",
    )


@pytest.fixture
def education_entry(db, staff_profile):
    """
    Provide an education entry.

    Args:
        staff_profile: Staff profile fixture

    Returns:
        EducationEntry: Education entry instance
    """
    from users.models import EducationEntry

    return EducationEntry.objects.create(
        public_profile=staff_profile,
        qualification_name="Test Degree",
        end_year=2019,
        institution="Test University",
        location="Test City",
    )


@pytest.fixture
def user_work(db, user, business_area):
    """
    Provide user work details.

    Args:
        user: User fixture
        business_area: Business area fixture

    Returns:
        UserWork: User work instance
    """
    from users.models import UserWork

    return UserWork.objects.create(
        user=user,
        business_area=business_area,
        role="DBCA Member",
    )


@pytest.fixture
def user_factory():
    """
    Provide UserFactory for creating users.

    Returns:
        UserFactory: Factory for creating users
    """
    return UserFactory


@pytest.fixture
def api_client():
    """
    Provide API client for view tests.

    Returns:
        APIClient: REST framework API client
    """
    from rest_framework.test import APIClient

    return APIClient()
