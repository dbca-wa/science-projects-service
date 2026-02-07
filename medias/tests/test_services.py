"""
Tests for media services
"""

import pytest
from rest_framework.exceptions import NotFound, PermissionDenied

from medias.models import (
    AgencyImage,
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    LegacyAnnualReportPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
    UserAvatar,
)
from medias.services.media_service import MediaService


class TestProjectDocumentPDFService:
    """Tests for project document PDF service operations"""

    def test_list_project_document_pdfs(self, project_document_pdf, db):
        """Test listing project document PDFs"""
        # Act
        pdfs = MediaService.list_project_document_pdfs()

        # Assert
        assert pdfs.count() == 1
        assert project_document_pdf in pdfs

    def test_get_project_document_pdf(self, project_document_pdf, db):
        """Test getting project document PDF by ID"""
        # Act
        result = MediaService.get_project_document_pdf(project_document_pdf.id)

        # Assert
        assert result == project_document_pdf

    def test_get_project_document_pdf_not_found(self, db):
        """Test getting non-existent PDF raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Project document PDF 999 not found"):
            MediaService.get_project_document_pdf(999)


class TestAnnualReportPDFService:
    """Tests for annual report PDF service operations"""

    def test_list_annual_report_pdfs(self, annual_report_pdf, db):
        """Test listing annual report PDFs"""
        # Act
        pdfs = MediaService.list_annual_report_pdfs()

        # Assert
        assert pdfs.count() == 1
        assert annual_report_pdf in pdfs

    def test_get_annual_report_pdf(self, annual_report_pdf, db):
        """Test getting annual report PDF by ID"""
        # Act
        result = MediaService.get_annual_report_pdf(annual_report_pdf.id)

        # Assert
        assert result == annual_report_pdf

    def test_get_annual_report_pdf_not_found(self, db):
        """Test getting non-existent PDF raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Annual report PDF 999 not found"):
            MediaService.get_annual_report_pdf(999)

    def test_create_annual_report_pdf(self, annual_report, user, mock_file, db):
        """Test creating annual report PDF"""
        # Arrange
        data = {
            "file": mock_file,
            "report": annual_report,
            "creator": user,
        }

        # Act
        pdf = MediaService.create_annual_report_pdf(user, data)

        # Assert
        assert pdf.id is not None
        assert pdf.report == annual_report
        assert pdf.creator == user

    def test_update_annual_report_pdf(self, annual_report_pdf, user, mock_file, db):
        """Test updating annual report PDF"""
        # Arrange
        data = {"file": mock_file}

        # Act
        updated = MediaService.update_annual_report_pdf(
            annual_report_pdf.id, user, data
        )

        # Assert
        assert updated.file is not None

    def test_delete_annual_report_pdf(self, annual_report_pdf, user, db):
        """Test deleting annual report PDF"""
        # Arrange
        pdf_id = annual_report_pdf.id

        # Act
        MediaService.delete_annual_report_pdf(pdf_id, user)

        # Assert
        assert not AnnualReportPDF.objects.filter(id=pdf_id).exists()


class TestLegacyAnnualReportPDFService:
    """Tests for legacy annual report PDF service operations"""

    def test_list_legacy_annual_report_pdfs(self, legacy_annual_report_pdf, db):
        """Test listing legacy annual report PDFs"""
        # Act
        pdfs = MediaService.list_legacy_annual_report_pdfs()

        # Assert
        assert pdfs.count() == 1
        assert legacy_annual_report_pdf in pdfs

    def test_get_legacy_annual_report_pdf(self, legacy_annual_report_pdf, db):
        """Test getting legacy annual report PDF by ID"""
        # Act
        result = MediaService.get_legacy_annual_report_pdf(legacy_annual_report_pdf.id)

        # Assert
        assert result == legacy_annual_report_pdf

    def test_get_legacy_annual_report_pdf_not_found(self, db):
        """Test getting non-existent PDF raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Legacy annual report PDF 999 not found"):
            MediaService.get_legacy_annual_report_pdf(999)

    def test_create_legacy_annual_report_pdf(self, user, mock_file, db):
        """Test creating legacy annual report PDF"""
        # Arrange
        data = {
            "file": mock_file,
            "year": 2010,
            "creator": user,
        }

        # Act
        pdf = MediaService.create_legacy_annual_report_pdf(user, data)

        # Assert
        assert pdf.id is not None
        assert pdf.year == 2010
        assert pdf.creator == user

    def test_update_legacy_annual_report_pdf(self, legacy_annual_report_pdf, user, db):
        """Test updating legacy annual report PDF"""
        # Arrange
        data = {"year": 2016}

        # Act
        updated = MediaService.update_legacy_annual_report_pdf(
            legacy_annual_report_pdf.id, user, data
        )

        # Assert
        assert updated.year == 2016

    def test_delete_legacy_annual_report_pdf(self, legacy_annual_report_pdf, user, db):
        """Test deleting legacy annual report PDF"""
        # Arrange
        pdf_id = legacy_annual_report_pdf.id

        # Act
        MediaService.delete_legacy_annual_report_pdf(pdf_id, user)

        # Assert
        assert not LegacyAnnualReportPDF.objects.filter(id=pdf_id).exists()


class TestAnnualReportMediaService:
    """Tests for annual report media service operations"""

    def test_list_annual_report_media(self, annual_report_media, db):
        """Test listing annual report media"""
        # Act
        media = MediaService.list_annual_report_media()

        # Assert
        assert media.count() == 1
        assert annual_report_media in media

    def test_get_annual_report_media(self, annual_report_media, db):
        """Test getting annual report media by ID"""
        # Act
        result = MediaService.get_annual_report_media(annual_report_media.id)

        # Assert
        assert result == annual_report_media

    def test_get_annual_report_media_not_found(self, db):
        """Test getting non-existent media raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Annual report media 999 not found"):
            MediaService.get_annual_report_media(999)

    def test_get_annual_report_media_by_report_and_kind(
        self, annual_report_media, annual_report, db
    ):
        """Test getting annual report media by report and kind"""
        # Act
        result = MediaService.get_annual_report_media_by_report_and_kind(
            annual_report.id, AnnualReportMedia.MediaTypes.COVER
        )

        # Assert
        assert result == annual_report_media

    def test_get_annual_report_media_by_report_and_kind_not_found(
        self, annual_report, db
    ):
        """Test getting non-existent media by report and kind returns None"""
        # Act
        result = MediaService.get_annual_report_media_by_report_and_kind(
            annual_report.id, AnnualReportMedia.MediaTypes.REAR_COVER
        )

        # Assert
        assert result is None

    def test_create_annual_report_media(self, annual_report, user, mock_image, db):
        """Test creating annual report media"""
        # Arrange
        data = {
            "file": mock_image,
            "kind": AnnualReportMedia.MediaTypes.REAR_COVER,
            "report": annual_report,
            "uploader": user,
        }

        # Act
        media = MediaService.create_annual_report_media(user, data)

        # Assert
        assert media.id is not None
        assert media.kind == AnnualReportMedia.MediaTypes.REAR_COVER
        assert media.report == annual_report

    def test_update_annual_report_media(self, annual_report_media, user, db):
        """Test updating annual report media"""
        # Arrange
        data = {"kind": AnnualReportMedia.MediaTypes.SDCHART}

        # Act
        updated = MediaService.update_annual_report_media(
            annual_report_media.id, user, data
        )

        # Assert
        assert updated.kind == AnnualReportMedia.MediaTypes.SDCHART

    def test_delete_annual_report_media(self, annual_report_media, user, db):
        """Test deleting annual report media"""
        # Arrange
        media_id = annual_report_media.id

        # Act
        MediaService.delete_annual_report_media(media_id, user)

        # Assert
        assert not AnnualReportMedia.objects.filter(id=media_id).exists()

    def test_delete_annual_report_media_by_report_and_kind(
        self, annual_report_media, annual_report, user, db
    ):
        """Test deleting annual report media by report and kind"""
        # Act
        MediaService.delete_annual_report_media_by_report_and_kind(
            annual_report.id, AnnualReportMedia.MediaTypes.COVER, user
        )

        # Assert
        assert not AnnualReportMedia.objects.filter(id=annual_report_media.id).exists()


class TestBusinessAreaPhotoService:
    """Tests for business area photo service operations"""

    def test_list_business_area_photos(self, business_area_photo, db):
        """Test listing business area photos"""
        # Act
        photos = MediaService.list_business_area_photos()

        # Assert
        assert photos.count() == 1
        assert business_area_photo in photos

    def test_get_business_area_photo(self, business_area_photo, db):
        """Test getting business area photo by ID"""
        # Act
        result = MediaService.get_business_area_photo(business_area_photo.id)

        # Assert
        assert result == business_area_photo

    def test_get_business_area_photo_not_found(self, db):
        """Test getting non-existent photo raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Business area photo 999 not found"):
            MediaService.get_business_area_photo(999)

    def test_create_business_area_photo(self, business_area, user, mock_image, db):
        """Test creating business area photo"""
        # Arrange
        data = {
            "file": mock_image,
            "business_area": business_area,
            "uploader": user,
        }

        # Act
        photo = MediaService.create_business_area_photo(user, data)

        # Assert
        assert photo.id is not None
        assert photo.business_area == business_area
        assert photo.uploader == user

    def test_update_business_area_photo_as_uploader(
        self, business_area_photo, user, mock_image, db
    ):
        """Test updating business area photo as uploader"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_business_area_photo(
            business_area_photo.id, user, data
        )

        # Assert
        assert updated.file is not None

    def test_update_business_area_photo_as_superuser(
        self, business_area_photo, superuser, mock_image, db
    ):
        """Test updating business area photo as superuser"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_business_area_photo(
            business_area_photo.id, superuser, data
        )

        # Assert
        assert updated.file is not None

    def test_update_business_area_photo_permission_denied(
        self, business_area_photo, db
    ):
        """Test updating business area photo without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        data = {"size": 5000}

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.update_business_area_photo(
                business_area_photo.id, other_user, data
            )

    def test_delete_business_area_photo_as_uploader(
        self, business_area_photo, user, db
    ):
        """Test deleting business area photo as uploader"""
        # Arrange
        photo_id = business_area_photo.id

        # Act
        MediaService.delete_business_area_photo(photo_id, user)

        # Assert
        assert not BusinessAreaPhoto.objects.filter(id=photo_id).exists()

    def test_delete_business_area_photo_permission_denied(
        self, business_area_photo, db
    ):
        """Test deleting business area photo without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.delete_business_area_photo(business_area_photo.id, other_user)


class TestProjectPhotoService:
    """Tests for project photo service operations"""

    def test_list_project_photos(self, project_photo, db):
        """Test listing project photos"""
        # Act
        photos = MediaService.list_project_photos()

        # Assert
        assert photos.count() == 1
        assert project_photo in photos

    def test_get_project_photo(self, project_photo, db):
        """Test getting project photo by ID"""
        # Act
        result = MediaService.get_project_photo(project_photo.id)

        # Assert
        assert result == project_photo

    def test_get_project_photo_not_found(self, db):
        """Test getting non-existent photo raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Project photo 999 not found"):
            MediaService.get_project_photo(999)

    def test_create_project_photo(self, project, user, mock_image, db):
        """Test creating project photo"""
        # Arrange
        data = {
            "file": mock_image,
            "project": project,
            "uploader": user,
        }

        # Act
        photo = MediaService.create_project_photo(user, data)

        # Assert
        assert photo.id is not None
        assert photo.project == project
        assert photo.uploader == user

    def test_update_project_photo_as_uploader(
        self, project_photo, user, mock_image, db
    ):
        """Test updating project photo as uploader"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_project_photo(project_photo.id, user, data)

        # Assert
        assert updated.file is not None

    def test_update_project_photo_as_superuser(
        self, project_photo, superuser, mock_image, db
    ):
        """Test updating project photo as superuser"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_project_photo(project_photo.id, superuser, data)

        # Assert
        assert updated.file is not None

    def test_update_project_photo_permission_denied(self, project_photo, db):
        """Test updating project photo without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        data = {"size": 4000}

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.update_project_photo(project_photo.id, other_user, data)

    def test_delete_project_photo_as_uploader(self, project_photo, user, db):
        """Test deleting project photo as uploader"""
        # Arrange
        photo_id = project_photo.id

        # Act
        MediaService.delete_project_photo(photo_id, user)

        # Assert
        assert not ProjectPhoto.objects.filter(id=photo_id).exists()

    def test_delete_project_photo_permission_denied(self, project_photo, db):
        """Test deleting project photo without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.delete_project_photo(project_photo.id, other_user)


class TestMethodologyPhotoService:
    """Tests for methodology photo service operations"""

    def test_list_methodology_photos(self, methodology_photo, db):
        """Test listing methodology photos"""
        # Act
        photos = MediaService.list_methodology_photos()

        # Assert
        assert photos.count() == 1
        assert methodology_photo in photos

    def test_get_methodology_photo_by_project_plan(
        self, methodology_photo, project_plan, db
    ):
        """Test getting methodology photo by project plan ID"""
        # Act
        result = MediaService.get_methodology_photo_by_project_plan(project_plan.id)

        # Assert
        assert result == methodology_photo

    def test_get_methodology_photo_by_project_plan_not_found(self, db):
        """Test getting non-existent photo returns None"""
        # Act
        result = MediaService.get_methodology_photo_by_project_plan(999)

        # Assert
        assert result is None

    def test_create_methodology_photo(self, project_plan, user, mock_image, db):
        """Test creating methodology photo"""
        # Arrange
        data = {
            "file": mock_image,
            "project_plan": project_plan,
            "uploader": user,
        }

        # Act
        photo = MediaService.create_methodology_photo(user, data)

        # Assert
        assert photo.id is not None
        assert photo.project_plan == project_plan
        assert photo.uploader == user

    def test_update_methodology_photo_as_uploader(
        self, methodology_photo, project_plan, user, mock_image, db
    ):
        """Test updating methodology photo as uploader"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_methodology_photo(project_plan.id, user, data)

        # Assert
        assert updated.file is not None

    def test_update_methodology_photo_as_superuser(
        self, methodology_photo, project_plan, superuser, mock_image, db
    ):
        """Test updating methodology photo as superuser"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_methodology_photo(
            project_plan.id, superuser, data
        )

        # Assert
        assert updated.file is not None

    def test_update_methodology_photo_not_found(self, user, db):
        """Test updating non-existent photo raises NotFound"""
        # Arrange
        data = {"size": 3000}

        # Act & Assert
        with pytest.raises(
            NotFound, match="Methodology photo for project plan 999 not found"
        ):
            MediaService.update_methodology_photo(999, user, data)

    def test_update_methodology_photo_permission_denied(
        self, methodology_photo, project_plan, db
    ):
        """Test updating methodology photo without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        data = {"size": 3500}

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.update_methodology_photo(project_plan.id, other_user, data)

    def test_delete_methodology_photo_as_uploader(
        self, methodology_photo, project_plan, user, db
    ):
        """Test deleting methodology photo as uploader"""
        # Arrange
        photo_id = methodology_photo.id

        # Act
        MediaService.delete_methodology_photo(project_plan.id, user)

        # Assert
        assert not ProjectPlanMethodologyPhoto.objects.filter(id=photo_id).exists()

    def test_delete_methodology_photo_not_found(self, user, db):
        """Test deleting non-existent methodology photo raises NotFound"""
        # Act & Assert
        with pytest.raises(
            NotFound, match="Methodology photo for project plan 999 not found"
        ):
            MediaService.delete_methodology_photo(999, user)

    def test_delete_methodology_photo_permission_denied(
        self, methodology_photo, project_plan, db
    ):
        """Test deleting methodology photo without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.delete_methodology_photo(project_plan.id, other_user)


class TestAgencyImageService:
    """Tests for agency image service operations"""

    def test_list_agency_images(self, agency_image, db):
        """Test listing agency images"""
        # Act
        images = MediaService.list_agency_images()

        # Assert
        assert images.count() == 1
        assert agency_image in images

    def test_get_agency_image(self, agency_image, db):
        """Test getting agency image by ID"""
        # Act
        result = MediaService.get_agency_image(agency_image.id)

        # Assert
        assert result == agency_image

    def test_get_agency_image_not_found(self, db):
        """Test getting non-existent image raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Agency image 999 not found"):
            MediaService.get_agency_image(999)

    def test_create_agency_image(self, agency, superuser, mock_image, db):
        """Test creating agency image"""
        # Arrange
        data = {
            "file": mock_image,
            "agency": agency,
        }

        # Act
        image = MediaService.create_agency_image(superuser, data)

        # Assert
        assert image.id is not None
        assert image.agency == agency

    def test_update_agency_image_as_superuser(
        self, agency_image, superuser, mock_image, db
    ):
        """Test updating agency image as superuser"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_agency_image(agency_image.id, superuser, data)

        # Assert
        assert updated.file is not None

    def test_update_agency_image_permission_denied(self, agency_image, user, db):
        """Test updating agency image as non-superuser raises PermissionDenied"""
        # Arrange
        data = {"size": 7000}

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.update_agency_image(agency_image.id, user, data)

    def test_delete_agency_image_as_superuser(self, agency_image, superuser, db):
        """Test deleting agency image as superuser"""
        # Arrange
        image_id = agency_image.id

        # Act
        MediaService.delete_agency_image(image_id, superuser)

        # Assert
        assert not AgencyImage.objects.filter(id=image_id).exists()

    def test_delete_agency_image_permission_denied(self, agency_image, user, db):
        """Test deleting agency image as non-superuser raises PermissionDenied"""
        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.delete_agency_image(agency_image.id, user)


class TestUserAvatarService:
    """Tests for user avatar service operations"""

    def test_list_user_avatars(self, user_avatar, db):
        """Test listing user avatars"""
        # Act
        avatars = MediaService.list_user_avatars()

        # Assert
        assert avatars.count() == 1
        assert user_avatar in avatars

    def test_get_user_avatar(self, user_avatar, db):
        """Test getting user avatar by ID"""
        # Act
        result = MediaService.get_user_avatar(user_avatar.id)

        # Assert
        assert result == user_avatar

    def test_get_user_avatar_not_found(self, db):
        """Test getting non-existent avatar raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="User avatar 999 not found"):
            MediaService.get_user_avatar(999)

    def test_create_user_avatar(self, user, mock_image, db):
        """Test creating user avatar"""
        # Arrange
        data = {
            "file": mock_image,
            "user": user,
        }

        # Act
        avatar = MediaService.create_user_avatar(user, data)

        # Assert
        assert avatar.id is not None
        assert avatar.user == user

    def test_update_user_avatar_as_owner(self, user_avatar, user, mock_image, db):
        """Test updating user avatar as owner"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_user_avatar(user_avatar.id, user, data)

        # Assert
        assert updated.file is not None

    def test_update_user_avatar_as_superuser(
        self, user_avatar, superuser, mock_image, db
    ):
        """Test updating user avatar as superuser"""
        # Arrange
        data = {"file": mock_image}

        # Act
        updated = MediaService.update_user_avatar(user_avatar.id, superuser, data)

        # Assert
        assert updated.file is not None

    def test_update_user_avatar_permission_denied(self, user_avatar, db):
        """Test updating user avatar without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        data = {"size": 3000}

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.update_user_avatar(user_avatar.id, other_user, data)

    def test_delete_user_avatar_as_owner(self, user_avatar, user, db):
        """Test deleting user avatar as owner"""
        # Arrange
        avatar_id = user_avatar.id

        # Act
        MediaService.delete_user_avatar(avatar_id, user)

        # Assert
        assert not UserAvatar.objects.filter(id=avatar_id).exists()

    def test_delete_user_avatar_as_superuser(self, user_avatar, superuser, db):
        """Test deleting user avatar as superuser"""
        # Arrange
        avatar_id = user_avatar.id

        # Act
        MediaService.delete_user_avatar(avatar_id, superuser)

        # Assert
        assert not UserAvatar.objects.filter(id=avatar_id).exists()

    def test_delete_user_avatar_permission_denied(self, user_avatar, db):
        """Test deleting user avatar without permission raises PermissionDenied"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )

        # Act & Assert
        with pytest.raises(PermissionDenied):
            MediaService.delete_user_avatar(user_avatar.id, other_user)
