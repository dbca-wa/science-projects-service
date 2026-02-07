"""
Tests for media views

NOTE: URL patterns in medias app use underscores (not hyphens) and no trailing slashes.
Base URL: /api/v1/medias/

URL Mapping:
- Annual Report PDFs: /api/v1/medias/report_pdfs, /api/v1/medias/report_pdfs/<int:pk>
- Legacy PDFs: /api/v1/medias/legacy_report_pdfs, /api/v1/medias/legacy_report_pdfs/<int:pk>
- Annual Report Media: /api/v1/medias/report_medias, /api/v1/medias/report_medias/<int:pk>
- Latest Report Media: /api/v1/medias/report_medias/latest/media
- Report Media Upload: /api/v1/medias/report_medias/<int:pk>/media
- Report Media Delete: /api/v1/medias/report_medias/<int:pk>/media/<str:section>
- User Avatars: /api/v1/medias/user_avatars, /api/v1/medias/user_avatars/<int:pk>
- Business Area Photos: /api/v1/medias/business_area_photos, /api/v1/medias/business_area_photos/<int:pk>
- Project Photos: /api/v1/medias/project_photos, /api/v1/medias/project_photos/<int:pk>
- Methodology Photos: /api/v1/medias/methodology_photos, /api/v1/medias/methodology_photos/<int:pk>
- Agency Photos: /api/v1/medias/agency_photos, /api/v1/medias/agency_photos/<int:pk>
- Project Document PDFs: NOT IN urls.py - needs to be added
"""

from rest_framework import status

from common.tests.test_helpers import medias_urls
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


class TestAnnualReportPDFViews:
    """Tests for annual report PDF views"""

    def test_list_annual_report_pdfs_authenticated(
        self, api_client, user, annual_report_pdf, db
    ):
        """Test listing annual report PDFs as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("report_pdfs"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_annual_report_pdfs_unauthenticated(self, api_client, db):
        """Test listing annual report PDFs without authentication"""
        # Act
        response = api_client.get(medias_urls.path("report_pdfs"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_annual_report_pdf_valid_data(
        self, api_client, user, annual_report, mock_file, db
    ):
        """Test creating annual report PDF with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_file,
            "report": annual_report.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("report_pdfs"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert AnnualReportPDF.objects.count() == 1

    def test_create_annual_report_pdf_invalid_data(self, api_client, user, db):
        """Test creating annual report PDF with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields

        # Act
        response = api_client.post(medias_urls.path("report_pdfs"), data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_annual_report_pdf_detail(
        self, api_client, user, annual_report_pdf, db
    ):
        """Test getting annual report PDF detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("report_pdfs", annual_report_pdf.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == annual_report_pdf.id

    def test_update_annual_report_pdf(self, api_client, user, annual_report_pdf, db):
        """Test updating annual report PDF"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"year": 2024}

        # Act
        response = api_client.put(
            medias_urls.path("report_pdfs", annual_report_pdf.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_annual_report_pdf(self, api_client, user, annual_report_pdf, db):
        """Test deleting annual report PDF"""
        # Arrange
        api_client.force_authenticate(user=user)
        pdf_id = annual_report_pdf.id

        # Act
        response = api_client.delete(medias_urls.path("report_pdfs", pdf_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AnnualReportPDF.objects.filter(id=pdf_id).exists()


class TestLegacyAnnualReportPDFViews:
    """Tests for legacy annual report PDF views"""

    def test_list_legacy_pdfs_authenticated(
        self, api_client, user, legacy_annual_report_pdf, db
    ):
        """Test listing legacy PDFs as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("legacy_report_pdfs"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_legacy_pdf_valid_data(self, api_client, user, mock_file, db):
        """Test creating legacy PDF with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_file,
            "year": 2010,
        }

        # Act
        response = api_client.post(
            medias_urls.path("legacy_report_pdfs"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert LegacyAnnualReportPDF.objects.count() == 1

    def test_get_legacy_pdf_detail(
        self, api_client, user, legacy_annual_report_pdf, db
    ):
        """Test getting legacy PDF detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            medias_urls.path("legacy_report_pdfs", legacy_annual_report_pdf.id)
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == legacy_annual_report_pdf.id

    def test_update_legacy_pdf(self, api_client, user, legacy_annual_report_pdf, db):
        """Test updating legacy PDF"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"year": 2016}

        # Act
        response = api_client.put(
            medias_urls.path("legacy_report_pdfs", legacy_annual_report_pdf.id),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_legacy_pdf(self, api_client, user, legacy_annual_report_pdf, db):
        """Test deleting legacy PDF"""
        # Arrange
        api_client.force_authenticate(user=user)
        pdf_id = legacy_annual_report_pdf.id

        # Act
        response = api_client.delete(medias_urls.path("legacy_report_pdfs", pdf_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LegacyAnnualReportPDF.objects.filter(id=pdf_id).exists()


class TestAnnualReportMediaViews:
    """Tests for annual report media views"""

    def test_list_annual_report_media_authenticated(
        self, api_client, user, annual_report_media, db
    ):
        """Test listing annual report media as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("report_medias"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_annual_report_media_valid_data(
        self, api_client, user, annual_report, mock_image, db
    ):
        """Test creating annual report media with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_image,
            "kind": AnnualReportMedia.MediaTypes.REAR_COVER,
            "report": annual_report.id,
            "uploader": user.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("report_medias"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_annual_report_media_detail(
        self, api_client, user, annual_report_media, db
    ):
        """Test getting annual report media detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            medias_urls.path("report_medias", annual_report_media.id)
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == annual_report_media.id

    def test_update_annual_report_media(
        self, api_client, user, annual_report_media, db
    ):
        """Test updating annual report media"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"kind": AnnualReportMedia.MediaTypes.SDCHART}

        # Act
        response = api_client.put(
            medias_urls.path("report_medias", annual_report_media.id),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_annual_report_media(
        self, api_client, user, annual_report_media, db
    ):
        """Test deleting annual report media"""
        # Arrange
        api_client.force_authenticate(user=user)
        media_id = annual_report_media.id

        # Act
        response = api_client.delete(medias_urls.path("report_medias", media_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AnnualReportMedia.objects.filter(id=media_id).exists()

    def test_get_latest_report_media(self, api_client, user, annual_report_media, db):
        """Test getting latest report's media"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("report_medias", "latest", "media"))

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_get_report_media_by_report(
        self, api_client, user, annual_report_media, annual_report, db
    ):
        """Test getting report media by report ID"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            medias_urls.path("report_medias", annual_report.id, "media")
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_upload_report_media_new(
        self, api_client, user, annual_report, mock_image, db
    ):
        """Test uploading new report media"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "section": AnnualReportMedia.MediaTypes.COVER,
            "file": mock_image,
        }

        # Act
        response = api_client.post(
            medias_urls.path("report_medias", annual_report.id, "media"),
            data,
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_report_media_update_existing(
        self, api_client, user, annual_report_media, annual_report, mock_image, db
    ):
        """Test updating existing report media"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "section": AnnualReportMedia.MediaTypes.COVER,
            "file": mock_image,
        }

        # Act
        response = api_client.post(
            medias_urls.path("report_medias", annual_report.id, "media"),
            data,
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_report_media_by_section(
        self, api_client, user, annual_report_media, annual_report, db
    ):
        """Test deleting report media by section"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.delete(
            medias_urls.path(
                "report_medias",
                annual_report.id,
                "media",
                AnnualReportMedia.MediaTypes.COVER,
            )
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestUserAvatarViews:
    """Tests for user avatar views"""

    def test_list_user_avatars_authenticated(self, api_client, user, user_avatar, db):
        """Test listing user avatars as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("user_avatars"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_user_avatars_unauthenticated(self, api_client, user_avatar, db):
        """Test listing user avatars without authentication (read-only)"""
        # Act
        response = api_client.get(medias_urls.path("user_avatars"))

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_avatar_valid_data(self, api_client, user, mock_image, db):
        """Test creating user avatar with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_image,
            "user": user.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("user_avatars"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_user_avatar_detail(self, api_client, user, user_avatar, db):
        """Test getting user avatar detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("user_avatars", user_avatar.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user_avatar.id

    def test_update_user_avatar_as_owner(self, api_client, user, user_avatar, db):
        """Test updating user avatar as owner"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"size": 5000}

        # Act
        response = api_client.put(
            medias_urls.path("user_avatars", user_avatar.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_user_avatar_as_superuser(
        self, api_client, superuser, user_avatar, db
    ):
        """Test updating user avatar as superuser"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        data = {"size": 5000}

        # Act
        response = api_client.put(
            medias_urls.path("user_avatars", user_avatar.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_user_avatar_permission_denied(self, api_client, user_avatar, db):
        """Test updating user avatar without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)
        data = {"size": 5000}

        # Act
        response = api_client.put(
            medias_urls.path("user_avatars", user_avatar.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_avatar_as_owner(self, api_client, user, user_avatar, db):
        """Test deleting user avatar as owner"""
        # Arrange
        api_client.force_authenticate(user=user)
        avatar_id = user_avatar.id

        # Act
        response = api_client.delete(medias_urls.path("user_avatars", avatar_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserAvatar.objects.filter(id=avatar_id).exists()

    def test_delete_user_avatar_permission_denied(self, api_client, user_avatar, db):
        """Test deleting user avatar without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)

        # Act
        response = api_client.delete(medias_urls.path("user_avatars", user_avatar.id))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBusinessAreaPhotoViews:
    """Tests for business area photo views"""

    def test_list_business_area_photos_authenticated(
        self, api_client, user, business_area_photo, db
    ):
        """Test listing business area photos as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("business_area_photos"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_business_area_photo_valid_data(
        self, api_client, user, business_area, mock_image, db
    ):
        """Test creating business area photo with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_image,
            "business_area": business_area.id,
            "uploader": user.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("business_area_photos"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_business_area_photo_detail(
        self, api_client, user, business_area_photo, db
    ):
        """Test getting business area photo detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            medias_urls.path("business_area_photos", business_area_photo.id)
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == business_area_photo.id

    def test_update_business_area_photo_as_uploader(
        self, api_client, user, business_area_photo, db
    ):
        """Test updating business area photo as uploader"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"size": 5000}

        # Act
        response = api_client.put(
            medias_urls.path("business_area_photos", business_area_photo.id),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_business_area_photo_permission_denied(
        self, api_client, business_area_photo, db
    ):
        """Test updating business area photo without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)
        data = {"size": 5000}

        # Act
        response = api_client.put(
            medias_urls.path("business_area_photos", business_area_photo.id),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_business_area_photo_as_uploader(
        self, api_client, user, business_area_photo, db
    ):
        """Test deleting business area photo as uploader"""
        # Arrange
        api_client.force_authenticate(user=user)
        photo_id = business_area_photo.id

        # Act
        response = api_client.delete(medias_urls.path("business_area_photos", photo_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BusinessAreaPhoto.objects.filter(id=photo_id).exists()

    def test_delete_business_area_photo_permission_denied(
        self, api_client, business_area_photo, db
    ):
        """Test deleting business area photo without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)

        # Act
        response = api_client.delete(
            medias_urls.path("business_area_photos", business_area_photo.id)
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectPhotoViews:
    """Tests for project photo views"""

    def test_list_project_photos_authenticated(
        self, api_client, user, project_photo, db
    ):
        """Test listing project photos as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("project_photos"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_project_photo_valid_data(
        self, api_client, user, project, mock_image, db
    ):
        """Test creating project photo with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_image,
            "project": project.id,
            "uploader": user.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("project_photos"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_project_photo_detail(self, api_client, user, project_photo, db):
        """Test getting project photo detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("project_photos", project_photo.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == project_photo.id

    def test_update_project_photo_as_uploader(
        self, api_client, user, project_photo, db
    ):
        """Test updating project photo as uploader"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"size": 4000}

        # Act
        response = api_client.put(
            medias_urls.path("project_photos", project_photo.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_project_photo_permission_denied(
        self, api_client, project_photo, db
    ):
        """Test updating project photo without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)
        data = {"size": 4000}

        # Act
        response = api_client.put(
            medias_urls.path("project_photos", project_photo.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_project_photo_as_uploader(
        self, api_client, user, project_photo, db
    ):
        """Test deleting project photo as uploader"""
        # Arrange
        api_client.force_authenticate(user=user)
        photo_id = project_photo.id

        # Act
        response = api_client.delete(medias_urls.path("project_photos", photo_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectPhoto.objects.filter(id=photo_id).exists()

    def test_delete_project_photo_permission_denied(
        self, api_client, project_photo, db
    ):
        """Test deleting project photo without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)

        # Act
        response = api_client.delete(
            medias_urls.path("project_photos", project_photo.id)
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMethodologyPhotoViews:
    """Tests for methodology photo views"""

    def test_list_methodology_photos_authenticated(
        self, api_client, user, methodology_photo, db
    ):
        """Test listing methodology photos as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("methodology_photos"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_methodology_photo_valid_data(
        self, api_client, user, project_plan, mock_image, db
    ):
        """Test creating methodology photo with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "pk": project_plan.id,
            "file": mock_image,
        }

        # Act
        response = api_client.post(
            medias_urls.path("methodology_photos"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_methodology_photo_detail(
        self, api_client, user, methodology_photo, project_plan, db
    ):
        """Test getting methodology photo detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            medias_urls.path("methodology_photos", project_plan.id)
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_update_methodology_photo_as_uploader(
        self, api_client, user, methodology_photo, project_plan, db
    ):
        """Test updating methodology photo as uploader"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"size": 3000}

        # Act
        response = api_client.put(
            medias_urls.path("methodology_photos", project_plan.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_methodology_photo_permission_denied(
        self, api_client, methodology_photo, project_plan, db
    ):
        """Test updating methodology photo without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)
        data = {"size": 3000}

        # Act
        response = api_client.put(
            medias_urls.path("methodology_photos", project_plan.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_methodology_photo_as_uploader(
        self, api_client, user, methodology_photo, project_plan, db
    ):
        """Test deleting methodology photo as uploader"""
        # Arrange
        api_client.force_authenticate(user=user)
        photo_id = methodology_photo.id

        # Act
        response = api_client.delete(
            medias_urls.path("methodology_photos", project_plan.id)
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectPlanMethodologyPhoto.objects.filter(id=photo_id).exists()

    def test_delete_methodology_photo_permission_denied(
        self, api_client, methodology_photo, project_plan, db
    ):
        """Test deleting methodology photo without permission"""
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass123"
        )
        api_client.force_authenticate(user=other_user)

        # Act
        response = api_client.delete(
            medias_urls.path("methodology_photos", project_plan.id)
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAgencyPhotoViews:
    """Tests for agency photo views"""

    def test_list_agency_photos_authenticated(self, api_client, user, agency_image, db):
        """Test listing agency photos as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("agency_photos"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_agency_photo_valid_data(
        self, api_client, superuser, agency, mock_image, db
    ):
        """Test creating agency photo with valid data"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        data = {
            "file": mock_image,
            "agency": agency.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("agency_photos"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_agency_photo_detail(self, api_client, user, agency_image, db):
        """Test getting agency photo detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("agency_photos", agency_image.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == agency_image.id

    def test_update_agency_photo_as_superuser(
        self, api_client, superuser, agency_image, db
    ):
        """Test updating agency photo as superuser"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        data = {"size": 7000}

        # Act
        response = api_client.put(
            medias_urls.path("agency_photos", agency_image.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_update_agency_photo_permission_denied(
        self, api_client, user, agency_image, db
    ):
        """Test updating agency photo as non-superuser"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"size": 7000}

        # Act
        response = api_client.put(
            medias_urls.path("agency_photos", agency_image.id), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_agency_photo_as_superuser(
        self, api_client, superuser, agency_image, db
    ):
        """Test deleting agency photo as superuser"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        image_id = agency_image.id

        # Act
        response = api_client.delete(medias_urls.path("agency_photos", image_id))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AgencyImage.objects.filter(id=image_id).exists()

    def test_delete_agency_photo_permission_denied(
        self, api_client, user, agency_image, db
    ):
        """Test deleting agency photo as non-superuser"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.delete(medias_urls.path("agency_photos", agency_image.id))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectDocumentPDFViews:
    """Tests for project document PDF views"""

    def test_list_project_document_pdfs_authenticated(
        self, api_client, user, project_document_pdf, db
    ):
        """Test listing project document PDFs as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(medias_urls.path("project_document_pdfs"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_project_document_pdf_valid_data(
        self, api_client, user, project, project_document, mock_file, db
    ):
        """Test creating project document PDF with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "file": mock_file,
            "project": project.id,
            "document": project_document.id,
        }

        # Act
        response = api_client.post(
            medias_urls.path("project_document_pdfs"), data, format="multipart"
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
