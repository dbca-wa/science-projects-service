"""
Details service - Project details management
"""

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound

from ..models import ExternalProjectDetails, ProjectDetail, StudentProjectDetails


class DetailsService:
    """Business logic for project details operations"""

    @staticmethod
    def get_project_details(project_id):
        """
        Get base project details with N+1 optimization

        Args:
            project_id: Project ID

        Returns:
            ProjectDetail instance

        Raises:
            NotFound: If details don't exist
        """
        try:
            return ProjectDetail.objects.select_related(
                "project",
                "creator",
                "creator__profile",
                "creator__work",
                "creator__work__business_area",
                "modifier",
                "modifier__profile",
                "modifier__work",
                "modifier__work__business_area",
                "owner",
                "owner__profile",
                "owner__work",
                "owner__work__business_area",
                "data_custodian",
                "data_custodian__profile",
                "data_custodian__work",
                "data_custodian__work__business_area",
                "site_custodian",
                "site_custodian__profile",
                "site_custodian__work",
                "site_custodian__work__business_area",
                "service",
            ).get(project_id=project_id)
        except ProjectDetail.DoesNotExist:
            raise NotFound(f"Project details not found for project {project_id}")

    @staticmethod
    def get_detail_by_project(project_id):
        """
        Alias for get_project_details for backward compatibility

        Args:
            project_id: Project ID

        Returns:
            ProjectDetail instance
        """
        return DetailsService.get_project_details(project_id)

    @staticmethod
    def get_student_details(detail_id):
        """
        Get student project details by detail ID

        Args:
            detail_id: StudentProjectDetails ID

        Returns:
            StudentProjectDetails instance or None
        """
        try:
            return StudentProjectDetails.objects.select_related("project").get(
                pk=detail_id
            )
        except StudentProjectDetails.DoesNotExist:
            return None

    @staticmethod
    def get_student_details_by_project(project_id):
        """
        Get student project details by project ID

        Args:
            project_id: Project ID

        Returns:
            StudentProjectDetails instance or None
        """
        try:
            return StudentProjectDetails.objects.select_related("project").get(
                project_id=project_id
            )
        except StudentProjectDetails.DoesNotExist:
            return None

    @staticmethod
    def get_external_details(detail_id):
        """
        Get external project details by detail ID

        Args:
            detail_id: ExternalProjectDetails ID

        Returns:
            ExternalProjectDetails instance or None
        """
        try:
            return ExternalProjectDetails.objects.select_related("project").get(
                pk=detail_id
            )
        except ExternalProjectDetails.DoesNotExist:
            return None

    @staticmethod
    def get_external_details_by_project(project_id):
        """
        Get external project details by project ID

        Args:
            project_id: Project ID

        Returns:
            ExternalProjectDetails instance or None
        """
        try:
            return ExternalProjectDetails.objects.select_related("project").get(
                project_id=project_id
            )
        except ExternalProjectDetails.DoesNotExist:
            return None

    @staticmethod
    def get_all_details(project_id):
        """
        Get all details for a project (base, student, external)

        Args:
            project_id: Project ID

        Returns:
            Dict with base, student, and external details
        """
        base_details = DetailsService.get_project_details(project_id)
        student_details = DetailsService.get_student_details_by_project(project_id)
        external_details = DetailsService.get_external_details_by_project(project_id)

        return {
            "base": base_details,
            "student": student_details,
            "external": external_details,
        }

    @staticmethod
    @transaction.atomic
    def create_project_details(project_id, data, user):
        """
        Create base project details

        Args:
            project_id: Project ID
            data: Details data
            user: User creating the details

        Returns:
            Created ProjectDetail instance
        """
        settings.LOGGER.info(f"{user} is creating details for project {project_id}")

        # Extract IDs from data (handle both ID and object inputs)
        def get_id(value):
            """Extract ID from value (handles both int and model instance)"""
            if value is None:
                return None
            return value.pk if hasattr(value, "pk") else value

        details = ProjectDetail.objects.create(
            project_id=project_id,
            creator_id=get_id(data.get("creator")),
            modifier_id=get_id(data.get("modifier", data.get("creator"))),
            owner_id=get_id(data.get("owner", data.get("creator"))),
            data_custodian_id=get_id(data.get("data_custodian")),
            site_custodian_id=get_id(data.get("site_custodian")),
            service_id=get_id(data.get("service")),
        )

        return details

    @staticmethod
    @transaction.atomic
    def update_project_details(project_id, data, user):
        """
        Update base project details

        Args:
            project_id: Project ID
            data: Updated details data
            user: User updating the details

        Returns:
            Updated ProjectDetail instance
        """
        details = DetailsService.get_project_details(project_id)
        settings.LOGGER.info(f"{user} is updating details for project {project_id}")

        # Update fields
        for field, value in data.items():
            if hasattr(details, field) and value is not None:
                setattr(details, field, value)

        details.save()
        return details

    @staticmethod
    @transaction.atomic
    def create_student_details(project_id, data, user):
        """
        Create student project details

        Args:
            project_id: Project ID
            data: Student details data
            user: User creating the details

        Returns:
            Created StudentProjectDetails instance
        """
        settings.LOGGER.info(
            f"{user} is creating student details for project {project_id}"
        )

        details = StudentProjectDetails.objects.create(
            project_id=project_id,
            level=data.get("level"),
            organisation=data.get("organisation"),
        )

        return details

    @staticmethod
    @transaction.atomic
    def update_student_details(project_id, data, user):
        """
        Update student project details

        Args:
            project_id: Project ID
            data: Updated student details data
            user: User updating the details

        Returns:
            Updated StudentProjectDetails instance
        """
        details = DetailsService.get_student_details_by_project(project_id)
        if not details:
            raise NotFound(f"Student details not found for project {project_id}")

        settings.LOGGER.info(
            f"{user} is updating student details for project {project_id}"
        )

        # Update fields
        for field, value in data.items():
            if hasattr(details, field) and value is not None:
                setattr(details, field, value)

        details.save()
        return details

    @staticmethod
    @transaction.atomic
    def create_external_details(project_id, data, user):
        """
        Create external project details

        Args:
            project_id: Project ID
            data: External details data
            user: User creating the details

        Returns:
            Created ExternalProjectDetails instance
        """
        settings.LOGGER.info(
            f"{user} is creating external details for project {project_id}"
        )

        details = ExternalProjectDetails.objects.create(
            project_id=project_id,
            collaboration_with=data.get(
                "collaboration_with", "<p>NO COLLABORATOR SET</p>"
            ),
            budget=data.get("budget", "<p>NO BUDGET SET</p>"),
            description=data.get("description", "<p>NO DESCRIPTION SET</p>"),
            aims=data.get("aims", "<p>NO AIMS SET</p>"),
        )

        return details

    @staticmethod
    @transaction.atomic
    def update_external_details(project_id, data, user):
        """
        Update external project details

        Args:
            project_id: Project ID
            data: Updated external details data
            user: User updating the details

        Returns:
            Updated ExternalProjectDetails instance
        """
        details = DetailsService.get_external_details_by_project(project_id)
        if not details:
            raise NotFound(f"External details not found for project {project_id}")

        settings.LOGGER.info(
            f"{user} is updating external details for project {project_id}"
        )

        # Update fields
        for field, value in data.items():
            if hasattr(details, field) and value is not None:
                setattr(details, field, value)

        details.save()
        return details

    @staticmethod
    def list_all_project_details():
        """List all project details"""
        return ProjectDetail.objects.all()

    @staticmethod
    def list_all_student_details():
        """List all student project details"""
        return StudentProjectDetails.objects.all()

    @staticmethod
    def list_all_external_details():
        """List all external project details"""
        return ExternalProjectDetails.objects.all()
