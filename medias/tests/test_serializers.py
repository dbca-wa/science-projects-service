"""
Tests for medias serializers
"""
import pytest
from unittest.mock import Mock, patch
from io import BytesIO
from PIL import Image

from medias.serializers import (
    ProjectDocumentPDFSerializer,
    ProjectDocumentPDFCreationSerializer,
    AECPDFSerializer,
    AECPDFCreateSerializer,
    TinyMethodologyImageSerializer,
    MethodologyImageCreateSerializer,
    MethodologyImageSerializer,
    TinyAnnualReportMediaSerializer,
    AnnualReportMediaSerializer,
    AnnualReportMediaCreationSerializer,
    TinyAnnualReportPDFSerializer,
    TinyLegacyAnnualReportPDFSerializer,
    AnnualReportPDFCreateSerializer,
    LegacyAnnualReportPDFCreateSerializer,
    AnnualReportPDFSerializer,
    LegacyAnnualReportPDFSerializer,
    TinyBusinessAreaPhotoSerializer,
    BusinessAreaPhotoSerializer,
    BusinessAreaPhotoCreateSerializer,
    TinyProjectPhotoSerializer,
    ProjectPhotoSerializer,
    ProjectPhotoCreateSerializer,
    TinyAgencyPhotoSerializer,
    AgencyPhotoSerializer,
    AgencyPhotoCreateSerializer,
    TinyUserAvatarSerializer,
    UserAvatarSerializer,
    UserAvatarCreateSerializer,
    StaffProfileAvatarSerializer,
)


class TestProjectDocumentPDFSerializers:
    """Tests for ProjectDocumentPDF serializers"""

    def test_project_document_pdf_serializer(self, project_document_pdf, db):
        """Test ProjectDocumentPDFSerializer"""
        serializer = ProjectDocumentPDFSerializer(project_document_pdf)
        data = serializer.data
        
        assert data['id'] == project_document_pdf.id
        assert 'file' in data
        assert data['document'] == project_document_pdf.document.id
        assert data['project'] == project_document_pdf.project.id

    def test_project_document_pdf_creation_serializer(self, project, project_document, mock_file, db):
        """Test ProjectDocumentPDFCreationSerializer"""
        data = {
            'file': mock_file,
            'document': project_document.id,
            'project': project.id,
        }
        serializer = ProjectDocumentPDFCreationSerializer(data=data)
        assert serializer.is_valid()


class TestAECPDFSerializers:
    """Tests for AECEndorsementPDF serializers"""

    def test_aec_pdf_serializer(self, aec_endorsement_pdf, db):
        """Test AECPDFSerializer"""
        serializer = AECPDFSerializer(aec_endorsement_pdf)
        data = serializer.data
        
        assert data['id'] == aec_endorsement_pdf.id
        assert 'file' in data

    def test_aec_pdf_create_serializer(self, endorsement, user, mock_file, db):
        """Test AECPDFCreateSerializer"""
        data = {
            'file': mock_file,
            'endorsement': endorsement.id,
            'creator': user.id,
        }
        serializer = AECPDFCreateSerializer(data=data)
        assert serializer.is_valid()
        
        pdf = serializer.save()
        assert pdf.id is not None
        assert pdf.endorsement == endorsement


class TestMethodologyImageSerializers:
    """Tests for ProjectPlanMethodologyPhoto serializers"""

    def test_tiny_methodology_image_serializer(self, methodology_photo, db):
        """Test TinyMethodologyImageSerializer"""
        serializer = TinyMethodologyImageSerializer(methodology_photo)
        data = serializer.data
        
        assert data['id'] == methodology_photo.id
        assert 'file' in data
        assert data['project_plan']['id'] == methodology_photo.project_plan.id
        assert data['uploader']['id'] == methodology_photo.uploader.id
        assert data['uploader']['username'] == methodology_photo.uploader.username

    def test_tiny_methodology_image_serializer_no_project_plan(self, db):
        """Test TinyMethodologyImageSerializer with no project_plan - COVERS LINE 58-59"""
        from medias.models import ProjectPlanMethodologyPhoto
        photo = Mock(spec=ProjectPlanMethodologyPhoto)
        photo.id = 1
        photo.file = Mock()
        photo.project_plan = None  # No project plan
        photo.uploader = None  # No uploader
        
        serializer = TinyMethodologyImageSerializer(photo)
        # Call get_project_plan directly to cover None case
        result = serializer.get_project_plan(photo)
        assert result is None  # Should return None when project_plan is None
        
        # Call get_uploader directly to cover None case
        result = serializer.get_uploader(photo)
        assert result is None  # Should return None when uploader is None

    def test_methodology_image_create_serializer(self, project_plan, user, mock_image, db):
        """Test MethodologyImageCreateSerializer"""
        data = {
            'file': mock_image,
            'project_plan': project_plan.id,
            'uploader': user.id,
        }
        serializer = MethodologyImageCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_methodology_image_serializer(self, methodology_photo, db):
        """Test MethodologyImageSerializer"""
        serializer = MethodologyImageSerializer(methodology_photo)
        data = serializer.data
        
        assert data['id'] == methodology_photo.id
        assert 'file' in data
        assert data['project_plan']['id'] == methodology_photo.project_plan.id
        assert data['uploader']['id'] == methodology_photo.uploader.id


class TestAnnualReportMediaSerializers:
    """Tests for AnnualReportMedia serializers"""

    def test_tiny_annual_report_media_serializer(self, annual_report_media, db):
        """Test TinyAnnualReportMediaSerializer"""
        serializer = TinyAnnualReportMediaSerializer(annual_report_media)
        data = serializer.data
        
        assert data['id'] == annual_report_media.id
        assert data['kind'] == annual_report_media.kind
        assert 'file' in data
        assert data['report']['id'] == annual_report_media.report.id
        assert data['report']['year'] == annual_report_media.report.year

    def test_tiny_annual_report_media_serializer_no_report(self, db):
        """Test TinyAnnualReportMediaSerializer with no report - COVERS LINE 146"""
        from medias.models import AnnualReportMedia
        media = Mock(spec=AnnualReportMedia)
        media.id = 1
        media.kind = 'cover'
        media.file = Mock()
        media.report = None  # No report
        
        serializer = TinyAnnualReportMediaSerializer(media)
        result = serializer.get_report(media)
        assert result is None  # Should return None when report is None

    def test_annual_report_media_serializer(self, annual_report_media, db):
        """Test AnnualReportMediaSerializer"""
        serializer = AnnualReportMediaSerializer(annual_report_media)
        data = serializer.data
        
        assert data['id'] == annual_report_media.id
        assert data['kind'] == annual_report_media.kind
        assert 'file' in data
        assert data['report']['id'] == annual_report_media.report.id

    def test_annual_report_media_serializer_no_report(self, db):
        """Test AnnualReportMediaSerializer with no report - COVERS LINE 163"""
        from medias.models import AnnualReportMedia
        media = Mock(spec=AnnualReportMedia)
        media.id = 1
        media.kind = 'cover'
        media.file = Mock()
        media.report = None  # No report
        
        serializer = AnnualReportMediaSerializer(media)
        result = serializer.get_report(media)
        assert result is None  # Should return None when report is None

    def test_annual_report_media_creation_serializer(self, annual_report, user, mock_image, db):
        """Test AnnualReportMediaCreationSerializer"""
        from medias.models import AnnualReportMedia
        data = {
            'file': mock_image,
            'kind': AnnualReportMedia.MediaTypes.COVER,
            'report': annual_report.id,
            'uploader': user.id,
        }
        serializer = AnnualReportMediaCreationSerializer(data=data)
        assert serializer.is_valid()


class TestAnnualReportPDFSerializers:
    """Tests for AnnualReportPDF serializers"""

    def test_tiny_annual_report_pdf_serializer(self, annual_report_pdf, db):
        """Test TinyAnnualReportPDFSerializer"""
        serializer = TinyAnnualReportPDFSerializer(annual_report_pdf)
        data = serializer.data
        
        assert data['id'] == annual_report_pdf.id
        assert 'file' in data
        assert data['report']['id'] == annual_report_pdf.report.id
        assert data['report']['year'] == annual_report_pdf.report.year

    def test_tiny_annual_report_pdf_serializer_no_report(self, db):
        """Test TinyAnnualReportPDFSerializer with no report - COVERS LINE 190"""
        from medias.models import AnnualReportPDF
        pdf = Mock(spec=AnnualReportPDF)
        pdf.id = 1
        pdf.file = Mock()
        pdf.report = None  # No report
        
        serializer = TinyAnnualReportPDFSerializer(pdf)
        result = serializer.get_report(pdf)
        assert result is None  # Should return None when report is None

    def test_tiny_legacy_annual_report_pdf_serializer(self, legacy_annual_report_pdf, db):
        """Test TinyLegacyAnnualReportPDFSerializer"""
        serializer = TinyLegacyAnnualReportPDFSerializer(legacy_annual_report_pdf)
        data = serializer.data
        
        assert data['id'] == legacy_annual_report_pdf.id
        assert 'file' in data
        assert data['year'] == legacy_annual_report_pdf.year
        assert data['report']['id'] == 0  # Always returns 0 for legacy
        assert data['report']['year'] == legacy_annual_report_pdf.year

    def test_annual_report_pdf_create_serializer(self, annual_report, user, mock_file, db):
        """Test AnnualReportPDFCreateSerializer"""
        data = {
            'file': mock_file,
            'report': annual_report.id,
            'creator': user.id,
        }
        serializer = AnnualReportPDFCreateSerializer(data=data)
        assert serializer.is_valid()
        
        pdf = serializer.save()
        assert pdf.id is not None
        assert pdf.report == annual_report

    def test_legacy_annual_report_pdf_create_serializer(self, user, mock_file, db):
        """Test LegacyAnnualReportPDFCreateSerializer"""
        data = {
            'file': mock_file,
            'year': 2015,
            'creator': user.id,
        }
        serializer = LegacyAnnualReportPDFCreateSerializer(data=data)
        assert serializer.is_valid()
        
        pdf = serializer.save()
        assert pdf.id is not None
        assert pdf.year == 2015

    def test_annual_report_pdf_serializer(self, annual_report_pdf, db):
        """Test AnnualReportPDFSerializer"""
        serializer = AnnualReportPDFSerializer(annual_report_pdf)
        data = serializer.data
        
        assert data['id'] == annual_report_pdf.id
        assert 'file' in data
        assert data['report']['id'] == annual_report_pdf.report.id
        assert data['report']['year'] == annual_report_pdf.report.year

    def test_annual_report_pdf_serializer_no_report(self, db):
        """Test AnnualReportPDFSerializer with no report - COVERS LINE 250"""
        from medias.models import AnnualReportPDF
        pdf = Mock(spec=AnnualReportPDF)
        pdf.id = 1
        pdf.file = Mock()
        pdf.report = None  # No report
        
        serializer = AnnualReportPDFSerializer(pdf)
        result = serializer.get_report(pdf)
        assert result is None  # Should return None when report is None

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_annual_report_pdf_serializer_file_not_found(self, mock_open, annual_report_pdf, db):
        """Test AnnualReportPDFSerializer when file not found - COVERS LINES 258-261"""
        serializer = AnnualReportPDFSerializer(annual_report_pdf)
        result = serializer.get_pdf_data(annual_report_pdf)
        assert result is None  # Should return None when file not found

    def test_annual_report_pdf_serializer_no_file(self, annual_report, user, db):
        """Test AnnualReportPDFSerializer with no file"""
        from medias.models import AnnualReportPDF
        pdf = AnnualReportPDF.objects.create(
            report=annual_report,
            creator=user,
            # No file
        )
        
        serializer = AnnualReportPDFSerializer(pdf)
        result = serializer.get_pdf_data(pdf)
        assert result is None  # Should return None when no file

    def test_legacy_annual_report_pdf_serializer(self, legacy_annual_report_pdf, db):
        """Test LegacyAnnualReportPDFSerializer"""
        serializer = LegacyAnnualReportPDFSerializer(legacy_annual_report_pdf)
        data = serializer.data
        
        assert data['id'] == legacy_annual_report_pdf.id
        assert 'file' in data
        assert data['year'] == legacy_annual_report_pdf.year

    def test_legacy_annual_report_pdf_serializer_no_file(self, user, db):
        """Test LegacyAnnualReportPDFSerializer with no file - COVERS LINE 277"""
        from medias.models import LegacyAnnualReportPDF
        pdf = LegacyAnnualReportPDF.objects.create(
            year=2015,
            creator=user,
            # No file
        )
        
        serializer = LegacyAnnualReportPDFSerializer(pdf)
        result = serializer.get_pdf_data(pdf)
        assert result is None  # Should return None when no file


class TestBusinessAreaPhotoSerializers:
    """Tests for BusinessAreaPhoto serializers"""

    def test_tiny_business_area_photo_serializer(self, business_area_photo, db):
        """Test TinyBusinessAreaPhotoSerializer"""
        serializer = TinyBusinessAreaPhotoSerializer(business_area_photo)
        data = serializer.data
        
        assert data['id'] == business_area_photo.id
        assert 'business_area' in data
        assert data['uploader']['id'] == business_area_photo.uploader.id

    def test_tiny_business_area_photo_serializer_no_uploader(self, business_area, mock_image, db):
        """Test TinyBusinessAreaPhotoSerializer with no uploader"""
        from medias.models import BusinessAreaPhoto
        photo = BusinessAreaPhoto.objects.create(
            file=mock_image,
            business_area=business_area,
            # No uploader
        )
        
        serializer = TinyBusinessAreaPhotoSerializer(photo)
        data = serializer.data
        assert data['uploader'] is None

    def test_business_area_photo_serializer(self, business_area_photo, db):
        """Test BusinessAreaPhotoSerializer"""
        serializer = BusinessAreaPhotoSerializer(business_area_photo)
        data = serializer.data
        
        assert data['id'] == business_area_photo.id
        assert 'business_area' in data
        assert data['uploader']['id'] == business_area_photo.uploader.id

    def test_business_area_photo_create_serializer(self, business_area, user, mock_image, db):
        """Test BusinessAreaPhotoCreateSerializer"""
        data = {
            'file': mock_image,
            'business_area': business_area.id,
            'uploader': user.id,
        }
        serializer = BusinessAreaPhotoCreateSerializer(data=data)
        assert serializer.is_valid()


class TestProjectPhotoSerializers:
    """Tests for ProjectPhoto serializers"""

    def test_tiny_project_photo_serializer(self, project_photo, db):
        """Test TinyProjectPhotoSerializer"""
        serializer = TinyProjectPhotoSerializer(project_photo)
        data = serializer.data
        
        assert data['id'] == project_photo.id
        assert 'file' in data
        assert data['project']['id'] == project_photo.project.id
        assert data['project']['title'] == project_photo.project.title
        assert data['uploader']['id'] == project_photo.uploader.id

    def test_tiny_project_photo_serializer_no_project(self, db):
        """Test TinyProjectPhotoSerializer with no project - COVERS LINE 357"""
        from medias.models import ProjectPhoto
        photo = Mock(spec=ProjectPhoto)
        photo.id = 1
        photo.file = Mock()
        photo.project = None  # No project
        photo.uploader = None  # No uploader
        
        serializer = TinyProjectPhotoSerializer(photo)
        result = serializer.get_project(photo)
        assert result is None  # Should return None when project is None
        
        result = serializer.get_uploader(photo)
        assert result is None  # Should return None when uploader is None

    def test_project_photo_serializer(self, project_photo, db):
        """Test ProjectPhotoSerializer"""
        serializer = ProjectPhotoSerializer(project_photo)
        data = serializer.data
        
        assert data['id'] == project_photo.id
        assert 'file' in data
        assert data['project']['id'] == project_photo.project.id

    def test_project_photo_serializer_no_project(self, db):
        """Test ProjectPhotoSerializer with no project - COVERS LINE 366"""
        from medias.models import ProjectPhoto
        photo = Mock(spec=ProjectPhoto)
        photo.id = 1
        photo.file = Mock()
        photo.project = None  # No project
        photo.uploader = None  # No uploader
        
        serializer = ProjectPhotoSerializer(photo)
        result = serializer.get_project(photo)
        assert result is None  # Should return None when project is None
        
        result = serializer.get_uploader(photo)
        assert result is None  # Should return None when uploader is None

    def test_project_photo_create_serializer(self, project, user, mock_image, db):
        """Test ProjectPhotoCreateSerializer"""
        data = {
            'file': mock_image,
            'project': project.id,
            'uploader': user.id,
        }
        serializer = ProjectPhotoCreateSerializer(data=data)
        assert serializer.is_valid()


class TestAgencyPhotoSerializers:
    """Tests for AgencyImage serializers"""

    def test_tiny_agency_photo_serializer(self, agency_image, db):
        """Test TinyAgencyPhotoSerializer"""
        serializer = TinyAgencyPhotoSerializer(agency_image)
        data = serializer.data
        
        assert data['id'] == agency_image.id
        assert 'file' in data
        assert data['agency']['id'] == agency_image.agency.id
        assert data['agency']['name'] == agency_image.agency.name

    def test_agency_photo_serializer(self, agency_image, db):
        """Test AgencyPhotoSerializer"""
        serializer = AgencyPhotoSerializer(agency_image)
        data = serializer.data
        
        assert data['id'] == agency_image.id
        assert 'file' in data
        assert data['agency']['id'] == agency_image.agency.id

    def test_agency_photo_create_serializer(self, agency, mock_image, db):
        """Test AgencyPhotoCreateSerializer"""
        data = {
            'file': mock_image,
            'agency': agency.id,
        }
        serializer = AgencyPhotoCreateSerializer(data=data)
        assert serializer.is_valid()


class TestUserAvatarSerializers:
    """Tests for UserAvatar serializers"""

    def test_tiny_user_avatar_serializer(self, user_avatar, db):
        """Test TinyUserAvatarSerializer"""
        serializer = TinyUserAvatarSerializer(user_avatar)
        data = serializer.data
        
        assert data['id'] == user_avatar.id
        assert 'file' in data
        assert data['user']['id'] == user_avatar.user.id
        assert data['user']['username'] == user_avatar.user.username

    def test_tiny_user_avatar_serializer_no_user(self, db):
        """Test TinyUserAvatarSerializer with no user - COVERS LINES 523-525"""
        from medias.models import UserAvatar
        avatar = Mock(spec=UserAvatar)
        avatar.id = 1
        avatar.file = Mock()
        avatar.user = None  # No user
        
        serializer = TinyUserAvatarSerializer(avatar)
        result = serializer.get_user(avatar)
        assert result is None  # Should return None when user is None

    def test_user_avatar_serializer(self, user_avatar, db):
        """Test UserAvatarSerializer"""
        serializer = UserAvatarSerializer(user_avatar)
        data = serializer.data
        
        assert data['id'] == user_avatar.id
        assert 'file' in data
        assert data['user']['id'] == user_avatar.user.id

    def test_user_avatar_create_serializer(self, user, mock_image, db):
        """Test UserAvatarCreateSerializer"""
        data = {
            'file': mock_image,
            'user': user.id,
        }
        serializer = UserAvatarCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_staff_profile_avatar_serializer(self, user_avatar, db):
        """Test StaffProfileAvatarSerializer"""
        serializer = StaffProfileAvatarSerializer(user_avatar)
        data = serializer.data
        
        assert data['id'] == user_avatar.id
        assert 'file' in data
        assert data['user']['id'] == user_avatar.user.id
