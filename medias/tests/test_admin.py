"""
Tests for medias admin
"""

from django.contrib.admin.sites import AdminSite

from medias.admin import (
    AECEndorsementPDFAdmin,
    AgencyImageAdmin,
    AgencyImageAdminForm,
    AnnualReportMediaAdmin,
    AnnualReportPDFAdmin,
    BusinessAreaPhotoAdmin,
    LegacyAnnualReportPDFAdmin,
    ProjectDocumentPDFAdmin,
    ProjectPhotoAdmin,
    ProjectPlanMethodologyPhotoAdmin,
    UserAvatarAdmin,
)
from medias.models import (
    AECEndorsementPDF,
    AgencyImage,
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    LegacyAnnualReportPDF,
    ProjectDocumentPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
    UserAvatar,
)


class TestAgencyImageAdminForm:
    """Tests for AgencyImageAdminForm"""

    def test_form_fields(self, db):
        """Test form has correct fields"""
        # Act
        form = AgencyImageAdminForm()

        # Assert
        assert "file" in form.fields
        assert form.fields["file"].required is True
        assert form.fields["file"].label == "Upload File"

    def test_form_meta_model(self, db):
        """Test form Meta model"""
        # Act
        form = AgencyImageAdminForm()

        # Assert
        assert form._meta.model == AgencyImage
        # Note: fields == "__all__" means all fields are included, not that _meta.fields == "__all__"


class TestAgencyImageAdmin:
    """Tests for AgencyImageAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())

        # Assert
        assert "agency" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display

    def test_form_class(self, db):
        """Test admin uses AgencyImageAdminForm"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())

        # Assert
        assert admin.form == AgencyImageAdminForm

    def test_size_in_mb_with_size(self, agency_image, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())
        # Refresh from DB to get actual size
        agency_image.refresh_from_db()

        # Act
        result = admin.size_in_mb(agency_image)

        # Assert
        # The fixture creates a small image, so size will be small
        assert "MB" in result
        assert result != "Unknown"

    def test_size_in_mb_without_size(self, agency_image, db):
        """Test size_in_mb method without size"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())
        # Manually set size to 0 to simulate no size
        agency_image.size = 0
        agency_image.save()

        # Act
        result = admin.size_in_mb(agency_image)

        # Assert
        # When size is 0, it shows "0.00 MB" not "Unknown"
        # Only None triggers "Unknown"
        assert result == "0.00 MB"

    def test_size_in_mb_attributes(self, db):
        """Test size_in_mb method attributes"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())

        # Assert
        assert hasattr(admin.size_in_mb, "admin_order_field")
        assert admin.size_in_mb.admin_order_field == "size"
        assert hasattr(admin.size_in_mb, "short_description")
        assert admin.size_in_mb.short_description == "Size (MB)"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions
        assert hasattr(admin, "recalculate_photo_sizes")
        assert callable(admin.recalculate_photo_sizes)

    def test_recalculate_photo_sizes_action_description(self, db):
        """Test recalculate_photo_sizes action description"""
        # Arrange
        admin = AgencyImageAdmin(AgencyImage, AdminSite())

        # Assert
        assert hasattr(admin.recalculate_photo_sizes, "short_description")
        assert (
            admin.recalculate_photo_sizes.short_description == "Recalculate photo sizes"
        )


class TestProjectDocumentPDFAdmin:
    """Tests for ProjectDocumentPDFAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = ProjectDocumentPDFAdmin(ProjectDocumentPDF, AdminSite())

        # Assert
        assert "pk" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "document" in admin.list_display
        assert "project" in admin.list_display

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = ProjectDocumentPDFAdmin(ProjectDocumentPDF, AdminSite())

        # Assert
        assert "project" in admin.search_fields

    def test_size_in_mb_with_size(self, project_document_pdf, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = ProjectDocumentPDFAdmin(ProjectDocumentPDF, AdminSite())
        project_document_pdf.refresh_from_db()

        # Act
        result = admin.size_in_mb(project_document_pdf)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_size_in_mb_without_size(self, project_document_pdf, db):
        """Test size_in_mb method without size"""
        # Arrange
        admin = ProjectDocumentPDFAdmin(ProjectDocumentPDF, AdminSite())
        project_document_pdf.size = 0
        project_document_pdf.save()

        # Act
        result = admin.size_in_mb(project_document_pdf)

        # Assert
        assert result == "0.00 MB"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = ProjectDocumentPDFAdmin(ProjectDocumentPDF, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestAECEndorsementPDFAdmin:
    """Tests for AECEndorsementPDFAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = AECEndorsementPDFAdmin(AECEndorsementPDF, AdminSite())

        # Assert
        assert "endorsement" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "creator" in admin.list_display

    def test_size_in_mb_with_size(self, aec_endorsement_pdf, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = AECEndorsementPDFAdmin(AECEndorsementPDF, AdminSite())
        aec_endorsement_pdf.refresh_from_db()

        # Act
        result = admin.size_in_mb(aec_endorsement_pdf)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = AECEndorsementPDFAdmin(AECEndorsementPDF, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestAnnualReportPDFAdmin:
    """Tests for AnnualReportPDFAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = AnnualReportPDFAdmin(AnnualReportPDF, AdminSite())

        # Assert
        assert "pk" in admin.list_display
        assert "report" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "creator" in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = AnnualReportPDFAdmin(AnnualReportPDF, AdminSite())

        # Assert
        assert "report" in admin.list_filter

    def test_size_in_mb_with_size(self, annual_report_pdf, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = AnnualReportPDFAdmin(AnnualReportPDF, AdminSite())
        annual_report_pdf.refresh_from_db()

        # Act
        result = admin.size_in_mb(annual_report_pdf)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = AnnualReportPDFAdmin(AnnualReportPDF, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestLegacyAnnualReportPDFAdmin:
    """Tests for LegacyAnnualReportPDFAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = LegacyAnnualReportPDFAdmin(LegacyAnnualReportPDF, AdminSite())

        # Assert
        assert "pk" in admin.list_display
        assert "year" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "creator" in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = LegacyAnnualReportPDFAdmin(LegacyAnnualReportPDF, AdminSite())

        # Assert
        assert "year" in admin.list_filter

    def test_size_in_mb_with_size(self, legacy_annual_report_pdf, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = LegacyAnnualReportPDFAdmin(LegacyAnnualReportPDF, AdminSite())
        legacy_annual_report_pdf.refresh_from_db()

        # Act
        result = admin.size_in_mb(legacy_annual_report_pdf)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = LegacyAnnualReportPDFAdmin(LegacyAnnualReportPDF, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestAnnualReportMediaAdmin:
    """Tests for AnnualReportMediaAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = AnnualReportMediaAdmin(AnnualReportMedia, AdminSite())

        # Assert
        assert "report" in admin.list_display
        assert "kind" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "uploader" in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = AnnualReportMediaAdmin(AnnualReportMedia, AdminSite())

        # Assert
        assert "report" in admin.list_filter
        assert "kind" in admin.list_filter

    def test_size_in_mb_with_size(self, annual_report_media, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = AnnualReportMediaAdmin(AnnualReportMedia, AdminSite())
        annual_report_media.refresh_from_db()

        # Act
        result = admin.size_in_mb(annual_report_media)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = AnnualReportMediaAdmin(AnnualReportMedia, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestBusinessAreaPhotoAdmin:
    """Tests for BusinessAreaPhotoAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = BusinessAreaPhotoAdmin(BusinessAreaPhoto, AdminSite())

        # Assert
        assert "pk" in admin.list_display
        assert "business_area" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "uploader" in admin.list_display

    def test_size_in_mb_with_size(self, business_area_photo, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = BusinessAreaPhotoAdmin(BusinessAreaPhoto, AdminSite())
        business_area_photo.refresh_from_db()

        # Act
        result = admin.size_in_mb(business_area_photo)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = BusinessAreaPhotoAdmin(BusinessAreaPhoto, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestProjectPhotoAdmin:
    """Tests for ProjectPhotoAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = ProjectPhotoAdmin(ProjectPhoto, AdminSite())

        # Assert
        assert "pk" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "project" in admin.list_display
        assert "uploader" in admin.list_display

    def test_size_in_mb_with_size(self, project_photo, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = ProjectPhotoAdmin(ProjectPhoto, AdminSite())
        project_photo.refresh_from_db()

        # Act
        result = admin.size_in_mb(project_photo)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = ProjectPhotoAdmin(ProjectPhoto, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestProjectPlanMethodologyPhotoAdmin:
    """Tests for ProjectPlanMethodologyPhotoAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = ProjectPlanMethodologyPhotoAdmin(
            ProjectPlanMethodologyPhoto, AdminSite()
        )

        # Assert
        assert "pk" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "project_plan" in admin.list_display
        assert "uploader" in admin.list_display

    def test_size_in_mb_with_size(self, methodology_photo, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = ProjectPlanMethodologyPhotoAdmin(
            ProjectPlanMethodologyPhoto, AdminSite()
        )
        methodology_photo.refresh_from_db()

        # Act
        result = admin.size_in_mb(methodology_photo)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = ProjectPlanMethodologyPhotoAdmin(
            ProjectPlanMethodologyPhoto, AdminSite()
        )

        # Assert
        assert "recalculate_photo_sizes" in admin.actions


class TestUserAvatarAdmin:
    """Tests for UserAvatarAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = UserAvatarAdmin(UserAvatar, AdminSite())

        # Assert
        assert "pk" in admin.list_display
        assert "file" in admin.list_display
        assert "size_in_mb" in admin.list_display
        assert "user" in admin.list_display

    def test_size_in_mb_with_size(self, user_avatar, db):
        """Test size_in_mb method with size"""
        # Arrange
        admin = UserAvatarAdmin(UserAvatar, AdminSite())
        user_avatar.refresh_from_db()

        # Act
        result = admin.size_in_mb(user_avatar)

        # Assert
        assert "MB" in result
        assert result != "Unknown"

    def test_size_in_mb_without_size(self, user_avatar, db):
        """Test size_in_mb method without size"""
        # Arrange
        admin = UserAvatarAdmin(UserAvatar, AdminSite())
        user_avatar.size = 0
        user_avatar.save()

        # Act
        result = admin.size_in_mb(user_avatar)

        # Assert
        assert result == "0.00 MB"

    def test_recalculate_photo_sizes_action_exists(self, db):
        """Test recalculate_photo_sizes action is configured"""
        # Arrange
        admin = UserAvatarAdmin(UserAvatar, AdminSite())

        # Assert
        assert "recalculate_photo_sizes" in admin.actions
