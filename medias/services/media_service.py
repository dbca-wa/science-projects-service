"""
Media service - Business logic for media operations
"""
from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied

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


class MediaService:
    """Business logic for media-related operations"""

    # Project Document PDF operations
    @staticmethod
    def list_project_document_pdfs():
        """List all project document PDFs"""
        return ProjectDocumentPDF.objects.all()

    @staticmethod
    def get_project_document_pdf(pk):
        """Get project document PDF by ID"""
        try:
            return ProjectDocumentPDF.objects.get(pk=pk)
        except ProjectDocumentPDF.DoesNotExist:
            raise NotFound(f"Project document PDF {pk} not found")

    # Annual Report PDF operations
    @staticmethod
    def list_annual_report_pdfs():
        """List all annual report PDFs"""
        return AnnualReportPDF.objects.all()

    @staticmethod
    def get_annual_report_pdf(pk):
        """Get annual report PDF by ID"""
        try:
            return AnnualReportPDF.objects.get(pk=pk)
        except AnnualReportPDF.DoesNotExist:
            raise NotFound(f"Annual report PDF {pk} not found")

    @staticmethod
    def create_annual_report_pdf(user, data):
        """Create annual report PDF"""
        settings.LOGGER.info(f"{user} is creating annual report PDF")
        return AnnualReportPDF.objects.create(**data)

    @staticmethod
    def update_annual_report_pdf(pk, user, data):
        """Update annual report PDF"""
        pdf = MediaService.get_annual_report_pdf(pk)
        settings.LOGGER.info(f"{user} is updating annual report PDF {pdf}")
        
        for field, value in data.items():
            setattr(pdf, field, value)
        pdf.save()
        
        return pdf

    @staticmethod
    def delete_annual_report_pdf(pk, user):
        """Delete annual report PDF"""
        pdf = MediaService.get_annual_report_pdf(pk)
        settings.LOGGER.info(f"{user} is deleting annual report PDF {pdf}")
        pdf.delete()

    # Legacy Annual Report PDF operations
    @staticmethod
    def list_legacy_annual_report_pdfs():
        """List all legacy annual report PDFs"""
        return LegacyAnnualReportPDF.objects.all()

    @staticmethod
    def get_legacy_annual_report_pdf(pk):
        """Get legacy annual report PDF by ID"""
        try:
            return LegacyAnnualReportPDF.objects.get(pk=pk)
        except LegacyAnnualReportPDF.DoesNotExist:
            raise NotFound(f"Legacy annual report PDF {pk} not found")

    @staticmethod
    def create_legacy_annual_report_pdf(user, data):
        """Create legacy annual report PDF"""
        settings.LOGGER.info(f"{user} is creating legacy annual report PDF")
        return LegacyAnnualReportPDF.objects.create(**data)

    @staticmethod
    def update_legacy_annual_report_pdf(pk, user, data):
        """Update legacy annual report PDF"""
        pdf = MediaService.get_legacy_annual_report_pdf(pk)
        settings.LOGGER.info(f"{user} is updating legacy annual report PDF {pdf}")
        
        for field, value in data.items():
            setattr(pdf, field, value)
        pdf.save()
        
        return pdf

    @staticmethod
    def delete_legacy_annual_report_pdf(pk, user):
        """Delete legacy annual report PDF"""
        pdf = MediaService.get_legacy_annual_report_pdf(pk)
        settings.LOGGER.info(f"{user} is deleting legacy annual report PDF {pdf}")
        pdf.delete()

    # Annual Report Media operations
    @staticmethod
    def list_annual_report_media():
        """List all annual report media"""
        return AnnualReportMedia.objects.all()

    @staticmethod
    def get_annual_report_media(pk):
        """Get annual report media by ID"""
        try:
            return AnnualReportMedia.objects.get(pk=pk)
        except AnnualReportMedia.DoesNotExist:
            raise NotFound(f"Annual report media {pk} not found")

    @staticmethod
    def get_annual_report_media_by_report_and_kind(report_pk, kind):
        """Get annual report media by report and kind"""
        try:
            return AnnualReportMedia.objects.filter(
                report=report_pk, kind=kind
            ).first()
        except AnnualReportMedia.DoesNotExist:
            raise NotFound(f"Annual report media not found")

    @staticmethod
    def create_annual_report_media(user, data):
        """Create annual report media"""
        settings.LOGGER.info(f"{user} is creating annual report media")
        return AnnualReportMedia.objects.create(**data)

    @staticmethod
    def update_annual_report_media(pk, user, data):
        """Update annual report media"""
        media = MediaService.get_annual_report_media(pk)
        settings.LOGGER.info(f"{user} is updating annual report media {media}")
        
        for field, value in data.items():
            setattr(media, field, value)
        media.save()
        
        return media

    @staticmethod
    def delete_annual_report_media(pk, user):
        """Delete annual report media"""
        media = MediaService.get_annual_report_media(pk)
        settings.LOGGER.info(f"{user} is deleting annual report media {media}")
        media.delete()

    @staticmethod
    def delete_annual_report_media_by_report_and_kind(report_pk, kind, user):
        """Delete annual report media by report and kind"""
        media = MediaService.get_annual_report_media_by_report_and_kind(report_pk, kind)
        if media:
            settings.LOGGER.info(f"{user} is deleting annual report media {media}")
            media.delete()

    # Business Area Photo operations
    @staticmethod
    def list_business_area_photos():
        """List all business area photos"""
        return BusinessAreaPhoto.objects.all()

    @staticmethod
    def get_business_area_photo(pk):
        """Get business area photo by ID"""
        try:
            return BusinessAreaPhoto.objects.get(pk=pk)
        except BusinessAreaPhoto.DoesNotExist:
            raise NotFound(f"Business area photo {pk} not found")

    @staticmethod
    def create_business_area_photo(user, data):
        """Create business area photo"""
        settings.LOGGER.info(f"{user} is creating business area photo")
        return BusinessAreaPhoto.objects.create(**data)

    @staticmethod
    def update_business_area_photo(pk, user, data):
        """Update business area photo"""
        photo = MediaService.get_business_area_photo(pk)
        
        # Check permissions
        if not (photo.uploader == user or user.is_superuser):
            settings.LOGGER.warning(f"{user} doesn't have permission to update {photo}")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is updating business area photo {photo}")
        
        for field, value in data.items():
            setattr(photo, field, value)
        photo.save()
        
        return photo

    @staticmethod
    def delete_business_area_photo(pk, user):
        """Delete business area photo"""
        photo = MediaService.get_business_area_photo(pk)
        
        # Check permissions
        if not (photo.uploader == user or user.is_superuser):
            settings.LOGGER.warning(f"{user} doesn't have permission to delete {photo}")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is deleting business area photo {photo}")
        photo.delete()

    # Project Photo operations
    @staticmethod
    def list_project_photos():
        """List all project photos"""
        return ProjectPhoto.objects.all()

    @staticmethod
    def get_project_photo(pk):
        """Get project photo by ID"""
        try:
            return ProjectPhoto.objects.get(pk=pk)
        except ProjectPhoto.DoesNotExist:
            raise NotFound(f"Project photo {pk} not found")

    @staticmethod
    def create_project_photo(user, data):
        """Create project photo"""
        settings.LOGGER.info(f"{user} is creating project photo")
        return ProjectPhoto.objects.create(**data)

    @staticmethod
    def update_project_photo(pk, user, data):
        """Update project photo"""
        photo = MediaService.get_project_photo(pk)
        
        # Check permissions
        if not (photo.uploader == user or user.is_superuser):
            settings.LOGGER.warning(f"{user} is not allowed to update project photo {photo}")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is updating project photo {photo}")
        
        for field, value in data.items():
            setattr(photo, field, value)
        photo.save()
        
        return photo

    @staticmethod
    def delete_project_photo(pk, user):
        """Delete project photo"""
        photo = MediaService.get_project_photo(pk)
        
        # Check permissions
        if not (photo.uploader == user or user.is_superuser):
            settings.LOGGER.warning(f"{user} is not allowed to delete project photo {photo}")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is deleting project photo {photo}")
        photo.delete()

    # Methodology Photo operations
    @staticmethod
    def list_methodology_photos():
        """List all methodology photos"""
        return ProjectPlanMethodologyPhoto.objects.all()

    @staticmethod
    def get_methodology_photo_by_project_plan(project_plan_pk):
        """Get methodology photo by project plan ID"""
        try:
            return ProjectPlanMethodologyPhoto.objects.get(project_plan=project_plan_pk)
        except ProjectPlanMethodologyPhoto.DoesNotExist:
            return None

    @staticmethod
    def create_methodology_photo(user, data):
        """Create methodology photo"""
        settings.LOGGER.info(f"{user} is creating methodology photo")
        return ProjectPlanMethodologyPhoto.objects.create(**data)

    @staticmethod
    def update_methodology_photo(project_plan_pk, user, data):
        """Update methodology photo"""
        photo = MediaService.get_methodology_photo_by_project_plan(project_plan_pk)
        
        if not photo:
            raise NotFound(f"Methodology photo for project plan {project_plan_pk} not found")
        
        # Check permissions
        if not (photo.uploader == user or user.is_superuser):
            settings.LOGGER.warning(f"{user} is not allowed to update methodology photo {photo}")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is updating methodology photo {photo}")
        
        for field, value in data.items():
            setattr(photo, field, value)
        photo.save()
        
        return photo

    @staticmethod
    def delete_methodology_photo(project_plan_pk, user):
        """Delete methodology photo"""
        photo = MediaService.get_methodology_photo_by_project_plan(project_plan_pk)
        
        if not photo:
            raise NotFound(f"Methodology photo for project plan {project_plan_pk} not found")
        
        # Check permissions
        if not (photo.uploader == user or user.is_superuser):
            settings.LOGGER.warning(f"{user} is not allowed to delete project photo {photo}")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is deleting methodology photo {photo}")
        photo.delete()

    # Agency Image operations
    @staticmethod
    def list_agency_images():
        """List all agency images"""
        return AgencyImage.objects.all()

    @staticmethod
    def get_agency_image(pk):
        """Get agency image by ID"""
        try:
            return AgencyImage.objects.get(pk=pk)
        except AgencyImage.DoesNotExist:
            raise NotFound(f"Agency image {pk} not found")

    @staticmethod
    def create_agency_image(user, data):
        """Create agency image"""
        settings.LOGGER.info(f"{user} is creating agency image")
        return AgencyImage.objects.create(**data)

    @staticmethod
    def update_agency_image(pk, user, data):
        """Update agency image"""
        image = MediaService.get_agency_image(pk)
        
        # Check permissions - only superusers
        if not user.is_superuser:
            settings.LOGGER.warning(f"{user} cannot update {image} as they are not a superuser")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is updating agency image {image}")
        
        for field, value in data.items():
            setattr(image, field, value)
        image.save()
        
        return image

    @staticmethod
    def delete_agency_image(pk, user):
        """Delete agency image"""
        image = MediaService.get_agency_image(pk)
        
        # Check permissions - only superusers
        if not user.is_superuser:
            settings.LOGGER.warning(f"{user} cannot delete {image} as they are not a superuser")
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is deleting agency image {image}")
        image.delete()

    # User Avatar operations
    @staticmethod
    def list_user_avatars():
        """List all user avatars"""
        return UserAvatar.objects.all()

    @staticmethod
    def get_user_avatar(pk):
        """Get user avatar by ID"""
        try:
            return UserAvatar.objects.get(pk=pk)
        except UserAvatar.DoesNotExist:
            raise NotFound(f"User avatar {pk} not found")

    @staticmethod
    def create_user_avatar(user, data):
        """Create user avatar"""
        settings.LOGGER.info(f"{user} is creating user avatar")
        return UserAvatar.objects.create(**data)

    @staticmethod
    def update_user_avatar(pk, user, data):
        """Update user avatar"""
        avatar = MediaService.get_user_avatar(pk)
        
        # Check permissions
        if not (user.is_superuser or user == avatar.user):
            settings.LOGGER.warning(
                f"Permission denied as {user} is not superuser and isn't the avatar owner of {avatar}"
            )
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is updating user avatar {avatar}")
        
        for field, value in data.items():
            setattr(avatar, field, value)
        avatar.save()
        
        return avatar

    @staticmethod
    def delete_user_avatar(pk, user):
        """Delete user avatar"""
        avatar = MediaService.get_user_avatar(pk)
        
        # Check permissions
        if not (user.is_superuser or user == avatar.user):
            settings.LOGGER.warning(
                f"Permission denied as {user} is not superuser and isn't the avatar owner of {avatar}"
            )
            raise PermissionDenied
        
        settings.LOGGER.info(f"{user} is deleting user avatar {avatar}")
        avatar.delete()
