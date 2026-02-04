"""
Pytest fixtures for categories tests
"""
import pytest
from rest_framework.test import APIClient

from categories.models import ProjectCategory
from users.models import User


@pytest.fixture
def api_client():
    """Provide API client for view tests"""
    return APIClient()


@pytest.fixture
def user(db):
    """Provide a regular user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )


@pytest.fixture
def project_category(db):
    """Provide a science project category"""
    return ProjectCategory.objects.create(
        name='Biodiversity',
        kind=ProjectCategory.CategoryKindChoices.SCIENCE,
    )


@pytest.fixture
def student_category(db):
    """Provide a student project category"""
    return ProjectCategory.objects.create(
        name='Student Research',
        kind=ProjectCategory.CategoryKindChoices.STUDENT,
    )


@pytest.fixture
def external_category(db):
    """Provide an external project category"""
    return ProjectCategory.objects.create(
        name='External Collaboration',
        kind=ProjectCategory.CategoryKindChoices.EXTERNAL,
    )


@pytest.fixture
def core_function_category(db):
    """Provide a core function project category"""
    return ProjectCategory.objects.create(
        name='Core Operations',
        kind=ProjectCategory.CategoryKindChoices.COREFUNCTION,
    )
