"""
Pytest fixtures for contacts app tests
"""
import pytest
from django.contrib.auth import get_user_model

from common.tests.factories import UserFactory
from agencies.models import Agency, Branch
from contacts.models import Address, UserContact, AgencyContact, BranchContact

User = get_user_model()


@pytest.fixture
def user(db):
    """Provide a regular user"""
    return UserFactory(
        username='testuser',
        email='test@example.com',
    )


@pytest.fixture
def agency(db, user):
    """Provide an agency"""
    return Agency.objects.create(
        name='Test Agency',
        key_stakeholder=user,
        is_active=True,
    )


@pytest.fixture
def branch(db, agency):
    """Provide a branch"""
    return Branch.objects.create(
        name='Test Branch',
        agency=agency,
        old_id=1,
    )


@pytest.fixture
def address_for_agency(db, agency):
    """Provide an address for an agency"""
    return Address.objects.create(
        agency=agency,
        street='123 Test St',
        suburb='Test Suburb',
        city='Test City',
        zipcode=12345,
        state='Test State',
        country='Test Country',
    )


@pytest.fixture
def address_for_branch(db, branch):
    """Provide an address for a branch"""
    return Address.objects.create(
        branch=branch,
        street='456 Branch St',
        suburb='Branch Suburb',
        city='Branch City',
        zipcode=67890,
        state='Branch State',
        country='Branch Country',
    )


@pytest.fixture
def user_contact(db, user):
    """Provide a user contact"""
    return UserContact.objects.create(
        user=user,
        email='user@example.com',
        phone='1234567890',
        alt_phone='0987654321',
        fax='1112223333',
    )


@pytest.fixture
def agency_contact(db, agency, address_for_agency):
    """Provide an agency contact"""
    return AgencyContact.objects.create(
        agency=agency,
        email='agency@example.com',
        phone='1234567890',
        alt_phone='0987654321',
        fax='1112223333',
        address=address_for_agency,
    )


@pytest.fixture
def branch_contact(db, branch, address_for_branch):
    """Provide a branch contact"""
    return BranchContact.objects.create(
        branch=branch,
        email='branch@example.com',
        phone='1234567890',
        alt_phone='0987654321',
        fax='1112223333',
        address=address_for_branch,
    )


@pytest.fixture
def user_factory():
    """Provide UserFactory for creating users"""
    return UserFactory
