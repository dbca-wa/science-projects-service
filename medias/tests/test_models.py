"""
Tests for medias models
"""
import pytest
from django.core.exceptions import ValidationError

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


class TestProjectDocumentPDF:
    """Tests for ProjectDocumentPDF model"""

    def test_create_project_document_pdf(self, project, project_document, mock_file, db):
        """Test creating project document PDF"""
        pdf = ProjectDocumentPDF.objects.create(
            file=mock_file,
            document=project_document,
            project=project,
        )
        
        assert pdf.id is not None
        assert pdf.document == project_document
        assert pdf.project == project
        assert pdf.size > 0  # Size auto-calculated from file

    def test_project_document_pdf_str(self, project_document_pdf, db):
        """Test __str__ method"""
        result = str(project_document_pdf)
        assert "PDF for" in result
        assert project_document_pdf.document.kind in result
        assert project_document_pdf.project.title in result

    def test_project_document_pdf_size_auto_calculation(self, project, project_document, mock_file, db):
        """Test size field is auto-calculated on save"""
        pdf = ProjectDocumentPDF(
            file=mock_file,
            document=project_document,
            project=project,
        )
        assert pdf.size == 0  # Before save
        
        pdf.save()
        assert pdf.size == mock_file.size  # After save


class TestAnnualReportMedia:
    """Tests for AnnualReportMedia model"""

    def test_create_annual_report_media(self, annual_report, user, mock_image, db):
        """Test creating annual report media"""
        media = AnnualReportMedia.objects.create(
            file=mock_image,
            kind=AnnualReportMedia.MediaTypes.COVER,
            report=annual_report,
            uploader=user,
        )
        
        assert media.id is not None
        assert media.kind == AnnualReportMedia.MediaTypes.COVER
        assert media.report == annual_report
        assert media.uploader == user
        assert media.size > 0

    def test_annual_report_media_str(self, annual_report_media, db):
        """Test __str__ method"""
        result = str(annual_report_media)
        assert str(annual_report_media.report.year) in result
        assert "Annual Report Media" in result

    def test_annual_report_media_unique_constraint(self, annual_report, user, mock_image, db):
        """Test unique constraint - one media per kind per report"""
        # Create first cover
        AnnualReportMedia.objects.create(
            file=mock_image,
            kind=AnnualReportMedia.MediaTypes.COVER,
            report=annual_report,
            uploader=user,
        )
        
        # Try to create second cover for same report
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            AnnualReportMedia.objects.create(
                file=mock_image,
                kind=AnnualReportMedia.MediaTypes.COVER,
                report=annual_report,
                uploader=user,
            )

    def test_annual_report_media_size_auto_calculation(self, annual_report, user, mock_image, db):
        """Test size field is auto-calculated on save"""
        media = AnnualReportMedia(
            file=mock_image,
            kind=AnnualReportMedia.MediaTypes.COVER,
            report=annual_report,
            uploader=user,
        )
        assert media.size == 0  # Before save
        
        media.save()
        assert media.size == mock_image.size  # After save


class TestAnnualReportPDF:
    """Tests for AnnualReportPDF model"""

    def test_create_annual_report_pdf(self, annual_report, user, mock_file, db):
        """Test creating annual report PDF"""
        pdf = AnnualReportPDF.objects.create(
            file=mock_file,
            report=annual_report,
            creator=user,
        )
        
        assert pdf.id is not None
        assert pdf.report == annual_report
        assert pdf.creator == user
        assert pdf.size > 0

    def test_annual_report_pdf_str(self, annual_report_pdf, db):
        """Test __str__ method"""
        result = str(annual_report_pdf)
        assert str(annual_report_pdf.report.year) in result
        assert "Annual Report PDF" in result

    def test_annual_report_pdf_size_auto_calculation(self, annual_report, user, mock_file, db):
        """Test size field is auto-calculated on save"""
        pdf = AnnualReportPDF(
            file=mock_file,
            report=annual_report,
            creator=user,
        )
        assert pdf.size == 0  # Before save
        
        pdf.save()
        assert pdf.size == mock_file.size  # After save


class TestLegacyAnnualReportPDF:
    """Tests for LegacyAnnualReportPDF model"""

    def test_create_legacy_annual_report_pdf(self, user, mock_file, db):
        """Test creating legacy annual report PDF"""
        pdf = LegacyAnnualReportPDF.objects.create(
            file=mock_file,
            year=2015,
            creator=user,
        )
        
        assert pdf.id is not None
        assert pdf.year == 2015
        assert pdf.creator == user
        assert pdf.size > 0

    def test_legacy_annual_report_pdf_str(self, legacy_annual_report_pdf, db):
        """Test __str__ method"""
        result = str(legacy_annual_report_pdf)
        assert str(legacy_annual_report_pdf.year) in result
        assert "Annual Report PDF" in result

    def test_legacy_annual_report_pdf_year_validation(self, user, mock_file, db):
        """Test year validation (2005-2019)"""
        # Valid year
        pdf = LegacyAnnualReportPDF.objects.create(
            file=mock_file,
            year=2010,
            creator=user,
        )
        assert pdf.year == 2010
        
        # Invalid year (too early)
        with pytest.raises(ValidationError):
            pdf = LegacyAnnualReportPDF(
                file=mock_file,
                year=2004,
                creator=user,
            )
            pdf.full_clean()
        
        # Invalid year (too late)
        with pytest.raises(ValidationError):
            pdf = LegacyAnnualReportPDF(
                file=mock_file,
                year=2020,
                creator=user,
            )
            pdf.full_clean()

    def test_legacy_annual_report_pdf_size_auto_calculation(self, user, mock_file, db):
        """Test size field is auto-calculated on save"""
        pdf = LegacyAnnualReportPDF(
            file=mock_file,
            year=2015,
            creator=user,
        )
        assert pdf.size == 0  # Before save
        
        pdf.save()
        assert pdf.size == mock_file.size  # After save


class TestAECEndorsementPDF:
    """Tests for AECEndorsementPDF model"""

    def test_create_aec_endorsement_pdf(self, endorsement, user, mock_file, db):
        """Test creating AEC endorsement PDF"""
        pdf = AECEndorsementPDF.objects.create(
            file=mock_file,
            endorsement=endorsement,
            creator=user,
        )
        
        assert pdf.id is not None
        assert pdf.endorsement == endorsement
        assert pdf.creator == user
        assert pdf.size > 0

    def test_aec_endorsement_pdf_str(self, aec_endorsement_pdf, db):
        """Test __str__ method"""
        result = str(aec_endorsement_pdf)
        assert "AEC PDF" in result

    def test_aec_endorsement_pdf_size_auto_calculation(self, endorsement, user, mock_file, db):
        """Test size field is auto-calculated on save - COVERS LINES 195-197"""
        pdf = AECEndorsementPDF(
            file=mock_file,
            endorsement=endorsement,
            creator=user,
        )
        assert pdf.size == 0  # Before save
        
        pdf.save()  # Lines 195-197 executed here
        assert pdf.size == mock_file.size  # After save


class TestProjectPhoto:
    """Tests for ProjectPhoto model"""

    def test_create_project_photo(self, project, user, mock_image, db):
        """Test creating project photo"""
        photo = ProjectPhoto.objects.create(
            file=mock_image,
            project=project,
            uploader=user,
        )
        
        assert photo.id is not None
        assert photo.project == project
        assert photo.uploader == user
        assert photo.size > 0

    def test_project_photo_str(self, project_photo, db):
        """Test __str__ method"""
        result = str(project_photo)
        assert "Project Photo File" in result

    def test_project_photo_size_auto_calculation(self, project, user, mock_image, db):
        """Test size field is auto-calculated on save"""
        photo = ProjectPhoto(
            file=mock_image,
            project=project,
            uploader=user,
        )
        assert photo.size == 0  # Before save
        
        photo.save()
        assert photo.size == mock_image.size  # After save


class TestProjectPlanMethodologyPhoto:
    """Tests for ProjectPlanMethodologyPhoto model"""

    def test_create_methodology_photo(self, project_plan, user, mock_image, db):
        """Test creating methodology photo"""
        photo = ProjectPlanMethodologyPhoto.objects.create(
            file=mock_image,
            project_plan=project_plan,
            uploader=user,
        )
        
        assert photo.id is not None
        assert photo.project_plan == project_plan
        assert photo.uploader == user
        assert photo.size > 0

    def test_methodology_photo_str(self, methodology_photo, db):
        """Test __str__ method"""
        result = str(methodology_photo)
        assert "Methodology Image File" in result

    def test_methodology_photo_size_auto_calculation(self, project_plan, user, mock_image, db):
        """Test size field is auto-calculated on save"""
        photo = ProjectPlanMethodologyPhoto(
            file=mock_image,
            project_plan=project_plan,
            uploader=user,
        )
        assert photo.size == 0  # Before save
        
        photo.save()
        assert photo.size == mock_image.size  # After save


class TestBusinessAreaPhoto:
    """Tests for BusinessAreaPhoto model"""

    def test_create_business_area_photo(self, business_area, user, mock_image, db):
        """Test creating business area photo"""
        photo = BusinessAreaPhoto.objects.create(
            file=mock_image,
            business_area=business_area,
            uploader=user,
        )
        
        assert photo.id is not None
        assert photo.business_area == business_area
        assert photo.uploader == user
        assert photo.size > 0

    def test_business_area_photo_str(self, business_area_photo, db):
        """Test __str__ method"""
        result = str(business_area_photo)
        assert "Business Area Photo File" in result

    def test_business_area_photo_size_auto_calculation(self, business_area, user, mock_image, db):
        """Test size field is auto-calculated on save"""
        photo = BusinessAreaPhoto(
            file=mock_image,
            business_area=business_area,
            uploader=user,
        )
        assert photo.size == 0  # Before save
        
        photo.save()
        assert photo.size == mock_image.size  # After save


class TestAgencyImage:
    """Tests for AgencyImage model"""

    def test_create_agency_image(self, agency, mock_image, db):
        """Test creating agency image"""
        image = AgencyImage.objects.create(
            file=mock_image,
            agency=agency,
        )
        
        assert image.id is not None
        assert image.agency == agency
        assert image.size > 0

    def test_agency_image_str(self, agency_image, db):
        """Test __str__ method"""
        result = str(agency_image)
        assert "Agency Photo File" in result

    def test_agency_image_size_auto_calculation(self, agency, mock_image, db):
        """Test size field is auto-calculated on save"""
        image = AgencyImage(
            file=mock_image,
            agency=agency,
        )
        assert image.size == 0  # Before save
        
        image.save()
        assert image.size == mock_image.size  # After save


class TestUserAvatar:
    """Tests for UserAvatar model"""

    def test_create_user_avatar(self, user, mock_image, db):
        """Test creating user avatar"""
        avatar = UserAvatar.objects.create(
            file=mock_image,
            user=user,
        )
        
        assert avatar.id is not None
        assert avatar.user == user
        assert avatar.size > 0

    def test_user_avatar_str(self, user_avatar, db):
        """Test __str__ method"""
        result = str(user_avatar)
        assert str(user_avatar.user) in result
        assert user_avatar.file.name in result

    def test_user_avatar_size_auto_calculation(self, user, mock_image, db):
        """Test size field is auto-calculated on save"""
        avatar = UserAvatar(
            file=mock_image,
            user=user,
        )
        assert avatar.size == 0  # Before save
        
        avatar.save()
        assert avatar.size == mock_image.size  # After save
