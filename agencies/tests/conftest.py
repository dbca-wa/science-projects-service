"""
Agencies app pytest fixtures
"""
import pytest
from agencies.models import (
    Affiliation,
    Agency,
    Branch,
    Division,
    BusinessArea,
    DepartmentalService,
)


@pytest.fixture
def affiliation(db):
    """Provide an affiliation"""
    return Affiliation.objects.create(name="Test Affiliation")


@pytest.fixture
def agency(db, user):
    """Provide an agency"""
    return Agency.objects.create(
        name="Test Agency",
        key_stakeholder=user,
        is_active=True,
    )


@pytest.fixture
def division(db, user):
    """Provide a division"""
    return Division.objects.create(
        name="Test Division",
        slug="test-division",
        director=user,
        approver=user,
    )


@pytest.fixture
def branch(db, agency, user):
    """Provide a branch"""
    return Branch.objects.create(
        agency=agency,
        name="Test Branch",
        manager=user,
    )


@pytest.fixture
def business_area(db, agency, division, user):
    """Provide a business area"""
    return BusinessArea.objects.create(
        agency=agency,
        name="Test Business Area",
        slug="test-ba",
        division=division,
        leader=user,
        finance_admin=user,
        data_custodian=user,
        caretaker=user,
        is_active=True,
        published=False,
    )


@pytest.fixture
def departmental_service(db, user):
    """Provide a departmental service"""
    return DepartmentalService.objects.create(
        name="Test Service",
        director=user,
    )
