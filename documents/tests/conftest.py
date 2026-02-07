"""
Document-specific pytest fixtures.

Provides fixtures for testing document-related functionality.
"""

import pytest
from django.contrib.auth import get_user_model

from common.tests.factories import (
    BusinessAreaFactory,
    ProjectDocumentFactory,
    ProjectFactory,
    UserFactory,
)

User = get_user_model()


@pytest.fixture
def project_lead(db):
    """
    Provide a project lead user.

    Returns:
        User: User instance configured as project lead
    """
    return UserFactory(
        username="project_lead",
        email="lead@example.com",
        first_name="Project",
        last_name="Lead",
    )


@pytest.fixture
def ba_lead(db):
    """
    Provide a business area lead user.

    Returns:
        User: User instance configured as BA lead
    """
    return UserFactory(
        username="ba_lead",
        email="ba_lead@example.com",
        first_name="BA",
        last_name="Lead",
    )


@pytest.fixture
def director(db):
    """
    Provide a director user (superuser).

    Returns:
        User: Superuser instance
    """
    return UserFactory(
        username="director",
        email="director@example.com",
        first_name="Director",
        last_name="User",
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def project_with_lead(db, project_lead):
    """
    Provide a project with a project lead.

    Args:
        project_lead: Project lead user fixture

    Returns:
        Project: Project instance with lead member
    """
    project = ProjectFactory()
    project.members.create(
        user=project_lead,
        is_leader=True,
        role="supervising",
    )
    return project


@pytest.fixture
def project_with_ba_lead(db, project_lead, ba_lead):
    """
    Provide a project with both project lead and BA lead.

    Args:
        project_lead: Project lead user fixture
        ba_lead: BA lead user fixture

    Returns:
        Project: Project instance with leads configured
    """
    business_area = BusinessAreaFactory(leader=ba_lead)
    project = ProjectFactory(business_area=business_area)
    project.members.create(
        user=project_lead,
        is_leader=True,
        role="supervising",
    )
    return project


@pytest.fixture
def concept_plan(db, project_with_lead):
    """
    Provide a concept plan document.

    Args:
        project_with_lead: Project with lead fixture

    Returns:
        ProjectDocument: Concept plan instance
    """
    return ProjectDocumentFactory(
        project=project_with_lead,
        kind="concept",
        status="new",
    )


@pytest.fixture
def project_plan(db, project_with_lead):
    """
    Provide a project plan document.

    Args:
        project_with_lead: Project with lead fixture

    Returns:
        ProjectDocument: Project plan instance
    """
    return ProjectDocumentFactory(
        project=project_with_lead,
        kind="projectplan",
        status="new",
    )


@pytest.fixture
def progress_report(db, project_with_lead, annual_report):
    """
    Provide a progress report with details.

    Args:
        project_with_lead: Project with lead fixture
        annual_report: Annual report fixture

    Returns:
        ProgressReport: Progress report instance with document
    """
    from documents.models import ProgressReport

    document = ProjectDocumentFactory(
        project=project_with_lead,
        kind="progressreport",
        status="new",
    )
    return ProgressReport.objects.create(
        document=document,
        project=project_with_lead,
        report=annual_report,
        year=annual_report.year,
        context="<p>Test context</p>",
        aims="<p>Test aims</p>",
        progress="<p>Test progress</p>",
        implications="<p>Test implications</p>",
        future="<p>Test future</p>",
    )


@pytest.fixture
def student_report(db, project_lead, annual_report):
    """
    Provide a student report with details.

    Args:
        project_lead: Project lead user fixture
        annual_report: Annual report fixture

    Returns:
        StudentReport: Student report instance with document
    """
    from documents.models import StudentReport

    # Create a student project
    student_project = ProjectFactory(kind="student")
    student_project.members.create(
        user=project_lead,
        is_leader=True,
        role="supervising",
    )
    document = ProjectDocumentFactory(
        project=student_project,
        kind="studentreport",
        status="new",
    )
    return StudentReport.objects.create(
        document=document,
        project=student_project,
        report=annual_report,
        year=annual_report.year,
        progress_report="<p>Test progress report</p>",
    )


@pytest.fixture
def project_document(db, project_with_lead):
    """
    Provide a generic project document.

    Args:
        project_with_lead: Project with lead fixture

    Returns:
        ProjectDocument: Generic document instance
    """
    return ProjectDocumentFactory(
        project=project_with_lead,
        kind="concept",
        status="new",
    )


@pytest.fixture
def user(db, project_lead):
    """
    Provide a generic user (alias for project_lead).

    Args:
        project_lead: Project lead user fixture

    Returns:
        User: User instance
    """
    return project_lead


@pytest.fixture
def project_member(db, project_with_lead, project_lead):
    """
    Provide a project member relationship.

    Args:
        project_with_lead: Project with lead fixture
        project_lead: Project lead user fixture

    Returns:
        ProjectMember: Project member instance
    """
    return project_with_lead.members.get(user=project_lead)


@pytest.fixture
def annual_report(db):
    """
    Provide an annual report.

    Returns:
        AnnualReport: Annual report instance
    """
    from datetime import date

    from documents.models import AnnualReport

    return AnnualReport.objects.create(
        year=2023,
        is_published=False,
        date_open=date(2023, 1, 1),  # Required field
        date_closed=date(2023, 12, 31),  # Required field
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


@pytest.fixture
def superuser(db):
    """
    Provide a superuser.

    Returns:
        User: Superuser instance
    """
    return UserFactory(
        username="superuser",
        email="superuser@example.com",
        first_name="Super",
        last_name="User",
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def admin_user(db):
    """
    Provide an admin user (staff with admin permissions).

    Returns:
        User: Admin user instance
    """
    return UserFactory(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        is_staff=True,
        is_superuser=False,
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
        employee_id="12345",
        is_hidden=False,
    )


@pytest.fixture
def business_area_with_leader(db, ba_lead):
    """
    Provide a business area with a leader.

    Args:
        ba_lead: BA lead user fixture

    Returns:
        BusinessArea: Business area instance with leader
    """
    return BusinessAreaFactory(leader=ba_lead)


@pytest.fixture
def user_with_work(db):
    """
    Provide a user with work relationship and business area.

    Returns:
        User: User instance with work relationship
    """
    from users.models import UserWork

    business_area = BusinessAreaFactory()
    user = UserFactory(
        username="user_with_work",
        email="work@example.com",
        is_staff=True,
    )
    UserWork.objects.create(
        user=user,
        business_area=business_area,
        role="DBCA",
    )
    return user


@pytest.fixture
def progress_report_with_details(db, project_with_lead, annual_report):
    """
    Provide a progress report with details.

    Args:
        project_with_lead: Project with lead fixture
        annual_report: Annual report fixture

    Returns:
        ProgressReport: Progress report instance with document
    """
    from documents.models import ProgressReport

    document = ProjectDocumentFactory(
        project=project_with_lead,
        kind="progressreport",
        status="new",
    )
    return ProgressReport.objects.create(
        document=document,
        project=project_with_lead,
        report=annual_report,
        year=annual_report.year,
        context="<p>Test context</p>",
        aims="<p>Test aims</p>",
        progress="<p>Test progress</p>",
        implications="<p>Test implications</p>",
        future="<p>Test future</p>",
    )


@pytest.fixture
def student_report_with_details(db, project_lead, annual_report):
    """
    Provide a student report with details.

    Args:
        project_lead: Project lead user fixture
        annual_report: Annual report fixture

    Returns:
        StudentReport: Student report instance with document
    """
    from documents.models import StudentReport

    # Create a student project
    student_project = ProjectFactory(kind="student")
    student_project.members.create(
        user=project_lead,
        is_leader=True,
        role="supervising",
    )
    document = ProjectDocumentFactory(
        project=student_project,
        kind="studentreport",
        status="new",
    )
    return StudentReport.objects.create(
        document=document,
        project=student_project,
        report=annual_report,
        year=annual_report.year,
        progress_report="<p>Test progress report</p>",
    )


@pytest.fixture
def project_closure(db, project_with_lead):
    """
    Provide a project closure with details.

    Args:
        project_with_lead: Project with lead fixture

    Returns:
        ProjectClosure: Project closure instance with document
    """
    from documents.models import ProjectClosure

    document = ProjectDocumentFactory(
        project=project_with_lead,
        kind="projectclosure",
        status="new",
    )
    return ProjectClosure.objects.create(
        document=document,
        project=project_with_lead,
        reason="<p>Test closure reason</p>",
    )


@pytest.fixture
def concept_plan_with_details(db, project_with_lead):
    """
    Provide a concept plan with details.

    Args:
        project_with_lead: Project with lead fixture

    Returns:
        ConceptPlan: Concept plan instance with document
    """
    from documents.models import ConceptPlan

    document = ProjectDocumentFactory(
        project=project_with_lead,
        kind="concept",
        status="new",
    )
    return ConceptPlan.objects.create(
        document=document,
        project=project_with_lead,
        background="<p>Test background</p>",
        aims="<p>Test aims</p>",
        outcome="<p>Test outcome</p>",
        collaborations="<p>Test collaborations</p>",
        strategic_context="<p>Test strategic context</p>",
    )


@pytest.fixture
def user_with_avatar(db):
    """
    Provide a user with an avatar.

    Returns:
        User: User instance with avatar attached
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    from medias.models import UserAvatar

    user = UserFactory(
        username="user_with_avatar",
        email="avatar@example.com",
    )

    # Create a simple test image file
    image_content = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    image_file = SimpleUploadedFile(
        name="test_avatar.gif", content=image_content, content_type="image/gif"
    )

    # Create avatar
    UserAvatar.objects.create(
        user=user,
        file=image_file,
    )

    return user


@pytest.fixture
def endorsement(db, project_plan_with_details):
    """
    Provide an endorsement for a project plan.

    Args:
        project_plan_with_details: Project plan with details fixture

    Returns:
        Endorsement: Endorsement instance
    """
    from documents.models import Endorsement

    return Endorsement.objects.create(
        project_plan=project_plan_with_details,
        ae_endorsement_required=True,
        ae_endorsement_provided=False,
        no_specimens="<p>Test specimens</p>",
        data_management="<p>Test data management</p>",
    )


@pytest.fixture
def project_plan_with_details(db, project_with_lead):
    """
    Provide a project plan with details.

    Args:
        project_with_lead: Project with lead fixture

    Returns:
        ProjectPlan: Project plan instance with document
    """
    from documents.models import ProjectPlan

    document = ProjectDocumentFactory(
        project=project_with_lead,
        kind="projectplan",
        status="new",
    )
    return ProjectPlan.objects.create(
        document=document,
        project=project_with_lead,
        background="<p>Test background</p>",
        aims="<p>Test aims</p>",
        outcome="<p>Test outcome</p>",
        knowledge_transfer="<p>Test knowledge transfer</p>",
        project_tasks="<p>Test project tasks</p>",
        listed_references="<p>Test references</p>",
        methodology="<p>Test methodology</p>",
    )
