"""
Medias app pytest fixtures
"""
import pytest
import datetime
from unittest.mock import Mock
from django.core.files.uploadedfile import SimpleUploadedFile

from medias.models import (
    ProjectDocumentPDF,
    AnnualReportMedia,
    AnnualReportPDF,
    LegacyAnnualReportPDF,
    AECEndorsementPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
    BusinessAreaPhoto,
    AgencyImage,
    UserAvatar,
)


@pytest.fixture
def mock_file():
    """Provide a mock file for testing"""
    return SimpleUploadedFile(
        "test_file.pdf",
        b"file_content",
        content_type="application/pdf"
    )


@pytest.fixture
def mock_image():
    """Provide a mock image for testing"""
    from PIL import Image
    from io import BytesIO
    
    # Create a simple 10x10 red image
    image = Image.new('RGB', (10, 10), color='red')
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    return SimpleUploadedFile(
        "test_image.jpg",
        image_io.read(),
        content_type="image/jpeg"
    )


@pytest.fixture
def project_document_pdf(db, project, project_document, mock_file):
    """Provide a project document PDF"""
    return ProjectDocumentPDF.objects.create(
        file=mock_file,
        document=project_document,
        project=project,
    )


@pytest.fixture
def annual_report_media(db, annual_report, user, mock_image):
    """Provide annual report media"""
    return AnnualReportMedia.objects.create(
        file=mock_image,
        kind=AnnualReportMedia.MediaTypes.COVER,
        report=annual_report,
        uploader=user,
    )


@pytest.fixture
def annual_report_pdf(db, annual_report, user, mock_file):
    """Provide annual report PDF"""
    return AnnualReportPDF.objects.create(
        file=mock_file,
        report=annual_report,
        creator=user,
    )


@pytest.fixture
def legacy_annual_report_pdf(db, user, mock_file):
    """Provide legacy annual report PDF"""
    return LegacyAnnualReportPDF.objects.create(
        file=mock_file,
        year=2015,
        creator=user,
    )


@pytest.fixture
def aec_endorsement_pdf(db, endorsement, user, mock_file):
    """Provide AEC endorsement PDF"""
    return AECEndorsementPDF.objects.create(
        file=mock_file,
        endorsement=endorsement,
        creator=user,
    )


@pytest.fixture
def project_photo(db, project, user, mock_image):
    """Provide project photo"""
    return ProjectPhoto.objects.create(
        file=mock_image,
        project=project,
        uploader=user,
    )


@pytest.fixture
def methodology_photo(db, project_plan, user, mock_image):
    """Provide methodology photo"""
    return ProjectPlanMethodologyPhoto.objects.create(
        file=mock_image,
        project_plan=project_plan,
        uploader=user,
    )


@pytest.fixture
def business_area_photo(db, business_area, user, mock_image):
    """Provide business area photo"""
    return BusinessAreaPhoto.objects.create(
        file=mock_image,
        business_area=business_area,
        uploader=user,
    )


@pytest.fixture
def agency_image(db, agency, mock_image):
    """Provide agency image"""
    return AgencyImage.objects.create(
        file=mock_image,
        agency=agency,
    )


@pytest.fixture
def user_avatar(db, user, mock_image):
    """Provide user avatar"""
    return UserAvatar.objects.create(
        file=mock_image,
        user=user,
    )


# Additional fixtures for related models (if not already in common fixtures)
@pytest.fixture
def project(db, business_area, user):
    """Provide a project"""
    from projects.models import Project
    return Project.objects.create(
        old_id=1,
        title="Test Project",
        business_area=business_area,
        status=Project.StatusChoices.NEW,
    )


@pytest.fixture
def project_document(db, project):
    """Provide a project document"""
    from documents.models import ProjectDocument
    return ProjectDocument.objects.create(
        old_id=1,
        project=project,
        kind=ProjectDocument.CategoryKindChoices.CONCEPTPLAN,
        status=ProjectDocument.StatusChoices.NEW,
    )


@pytest.fixture
def annual_report(db):
    """Provide an annual report"""
    from documents.models import AnnualReport
    return AnnualReport.objects.create(
        old_id=1,
        year=2023,
        date_open=datetime.date(2023, 1, 1),
        date_closed=datetime.date(2023, 12, 31),
    )


@pytest.fixture
def endorsement(db, project_plan):
    """Provide an endorsement"""
    from documents.models import Endorsement
    return Endorsement.objects.create(
        project_plan=project_plan,
    )


@pytest.fixture
def project_plan(db, project, project_document):
    """Provide a project plan"""
    from documents.models import ProjectPlan
    return ProjectPlan.objects.create(
        document=project_document,
        project=project,
    )


@pytest.fixture
def business_area(db, agency, division, user):
    """Provide a business area"""
    from agencies.models import BusinessArea
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
    )


@pytest.fixture
def agency(db, user):
    """Provide an agency"""
    from agencies.models import Agency
    return Agency.objects.create(
        name="Test Agency",
        key_stakeholder=user,
        is_active=True,
    )


@pytest.fixture
def division(db, user):
    """Provide a division"""
    from agencies.models import Division
    return Division.objects.create(
        old_id=1,
        name="Test Division",
        slug="test-division",
        director=user,
        approver=user,
    )
