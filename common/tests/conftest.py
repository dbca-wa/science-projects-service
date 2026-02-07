"""
Common pytest fixtures for backend testing.

Provides shared fixtures that can be used across all test files.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """
    Provide an API client for testing.

    Returns:
        APIClient: DRF API client instance
    """
    return APIClient()


@pytest.fixture
def user(db):
    """
    Provide a regular user.

    Returns:
        User: Regular user instance
    """
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
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
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """
    Provide an authenticated API client.

    Args:
        api_client: API client fixture
        user: User fixture

    Returns:
        APIClient: Authenticated API client
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, superuser):
    """
    Provide an admin API client.

    Args:
        api_client: API client fixture
        superuser: Superuser fixture

    Returns:
        APIClient: Admin-authenticated API client
    """
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def multiple_users(db):
    """
    Provide multiple test users.

    Returns:
        list[User]: List of 3 user instances
    """
    return [
        User.objects.create_user(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password="testpass123",
            first_name="User",
            last_name=f"{i}",
        )
        for i in range(1, 4)
    ]
