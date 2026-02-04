"""
Pytest fixtures for caretakers tests
"""
import pytest
from common.tests.factories import UserFactory, ProjectFactory, BusinessAreaFactory, DivisionFactory
from caretakers.models import Caretaker


@pytest.fixture
def caretaker_user(db):
    """Provide a caretaker user"""
    return UserFactory(
        username='caretaker',
        email='caretaker@example.com',
        first_name='Care',
        last_name='Taker',
    )


@pytest.fixture
def caretakee_user(db):
    """Provide a user being caretaken"""
    return UserFactory(
        username='caretakee',
        email='caretakee@example.com',
        first_name='Care',
        last_name='Takee',
    )


@pytest.fixture
def caretaker_assignment(db, caretaker_user, caretakee_user):
    """Provide a caretaker assignment"""
    return Caretaker.objects.create(
        user=caretakee_user,
        caretaker=caretaker_user,
        reason='Test caretaker assignment',
    )


@pytest.fixture
def directorate_user(db):
    """Provide a user in Directorate (identified by superuser status)"""
    # Directorate users are identified by is_superuser=True OR business_area.name=="Directorate"
    # Using superuser is simpler and avoids database constraint issues
    user = UserFactory(
        username='director',
        email='director@example.com',
        is_superuser=True,
    )
    
    return user


@pytest.fixture
def ba_leader_user(db):
    """Provide a business area leader"""
    user = UserFactory(
        username='ba_leader',
        email='ba_leader@example.com',
    )
    
    # Create business area with this user as leader
    business_area = BusinessAreaFactory(leader=user)
    
    return user


@pytest.fixture
def project_lead_user(db):
    """Provide a project lead user"""
    return UserFactory(
        username='project_lead',
        email='project_lead@example.com',
    )


@pytest.fixture
def team_member_user(db):
    """Provide a team member user"""
    return UserFactory(
        username='team_member',
        email='team_member@example.com',
    )
