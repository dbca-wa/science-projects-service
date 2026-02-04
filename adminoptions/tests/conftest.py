"""
Pytest fixtures for adminoptions app tests
"""
import pytest
from django.contrib.auth import get_user_model
from adminoptions.models import (
    AdminOptions,
    AdminTask,
    ContentField,
    GuideSection,
)
from caretakers.models import Caretaker  # Use caretakers app model, not adminoptions
from projects.models import Project, ProjectMember
from agencies.models import BusinessArea, Agency

User = get_user_model()


@pytest.fixture
def user(db):
    """Provide a regular user"""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def admin_user(db):
    """Provide an admin user"""
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def secondary_user(db):
    """Provide a secondary user for merge/caretaker operations"""
    return User.objects.create_user(
        username="secondary",
        email="secondary@example.com",
        password="testpass123",
        first_name="Secondary",
        last_name="User",
    )


@pytest.fixture
def admin_options(db, admin_user):
    """Provide an AdminOptions instance"""
    return AdminOptions.objects.create(
        email_options=AdminOptions.EmailOptions.ENABLED,
        maintainer=admin_user,
        guide_content={
            "test_field": "Test content",
            "another_field": "More content",
        },
    )


@pytest.fixture
def guide_section(db):
    """Provide a GuideSection instance"""
    return GuideSection.objects.create(
        id="test-section",
        title="Test Section",
        order=1,
        show_divider_after=True,
        category="test",
        is_active=True,
    )


@pytest.fixture
def content_field(db, guide_section):
    """Provide a ContentField instance"""
    return ContentField.objects.create(
        title="Test Field",
        field_key="test_field_key",
        description="Test field description",
        section=guide_section,
        order=1,
    )


@pytest.fixture
def business_area(db, user):
    """Provide a business area"""
    agency = Agency.objects.create(name="Test Agency")
    return BusinessArea.objects.create(
        name="Test Business Area",
        slug="test-business-area",
        agency=agency,
        leader=user,
        finance_admin=user,
        data_custodian=user,
        old_id=1,
    )


@pytest.fixture
def project(db, business_area):
    """Provide a project"""
    return Project.objects.create(
        title="Test Project",
        description="Test project description",
        business_area=business_area,
        status=Project.StatusChoices.NEW,
        kind=Project.CategoryKindChoices.SCIENCE,
        old_id=1,
    )


@pytest.fixture
def admin_task_delete_project(db, user, project):
    """Provide an AdminTask for project deletion"""
    return AdminTask.objects.create(
        action=AdminTask.ActionTypes.DELETEPROJECT,
        status=AdminTask.TaskStatus.PENDING,
        project=project,
        requester=user,
        reason="Test deletion reason",
    )


@pytest.fixture
def admin_task_merge_user(db, user, secondary_user):
    """Provide an AdminTask for user merge"""
    return AdminTask.objects.create(
        action=AdminTask.ActionTypes.MERGEUSER,
        status=AdminTask.TaskStatus.PENDING,
        primary_user=user,
        secondary_users=[secondary_user.pk],
        requester=user,
        reason="Test merge reason",
    )


@pytest.fixture
def admin_task_set_caretaker(db, user, secondary_user):
    """Provide an AdminTask for setting caretaker"""
    return AdminTask.objects.create(
        action=AdminTask.ActionTypes.SETCARETAKER,
        status=AdminTask.TaskStatus.PENDING,
        primary_user=user,
        secondary_users=[secondary_user.pk],
        requester=user,
        reason="Test caretaker reason",
    )


@pytest.fixture
def caretaker(db, user, secondary_user):
    """Provide a Caretaker instance"""
    return Caretaker.objects.create(
        user=user,
        caretaker=secondary_user,
        reason="Test caretaker reason",
    )
