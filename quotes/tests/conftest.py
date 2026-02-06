"""
Pytest fixtures for quotes app tests
"""
import pytest
from django.contrib.auth import get_user_model

from common.tests.factories import UserFactory
from quotes.models import Quote

User = get_user_model()


@pytest.fixture
def user(db):
    """Provide a regular user"""
    return UserFactory(
        username='testuser',
        email='test@example.com',
    )


@pytest.fixture
def quote(db):
    """Provide a quote"""
    return Quote.objects.create(
        text='Test quote text',
        author='Test Author',
    )


@pytest.fixture
def quote2(db):
    """Provide a second quote"""
    return Quote.objects.create(
        text='Another test quote',
        author='Another Author',
    )


@pytest.fixture
def user_factory():
    """Provide UserFactory for creating users"""
    return UserFactory
