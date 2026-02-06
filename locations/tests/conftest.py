"""
Pytest fixtures for locations app tests
"""
import pytest
from django.contrib.auth import get_user_model

from common.tests.factories import UserFactory
from locations.models import Area

User = get_user_model()


@pytest.fixture
def user(db):
    """Provide a regular user"""
    return UserFactory(
        username='testuser',
        email='test@example.com',
    )


@pytest.fixture
def dbca_region(db):
    """Provide a DBCA region area"""
    return Area.objects.create(
        name='Test DBCA Region',
        area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
    )


@pytest.fixture
def dbca_district(db):
    """Provide a DBCA district area"""
    return Area.objects.create(
        name='Test DBCA District',
        area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
    )


@pytest.fixture
def ibra_region(db):
    """Provide an IBRA region area"""
    return Area.objects.create(
        name='Test IBRA Region',
        area_type=Area.AreaTypeChoices.AREA_TYPE_IBRA_REGION,
    )


@pytest.fixture
def user_factory():
    """Provide UserFactory for creating users"""
    return UserFactory
