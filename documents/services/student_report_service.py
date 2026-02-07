"""
Student report service - Student report specific operations
"""

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .document_service import DocumentService


class StudentReportService:
    """Business logic for student report operations"""

    @staticmethod
    @transaction.atomic
    def create_student_report(user, project, year, data):
        """
        Create student report document

        Args:
            user: User creating the student report
            project: Project instance
            year: Report year
            data: Student report data

        Returns:
            ProjectDocument instance
        """
        settings.LOGGER.info(
            f"{user} is creating student report for project {project} year {year}"
        )

        # Create base document
        document = DocumentService.create_document(
            user=user, project=project, kind="studentreport", data=data
        )

        return document

    @staticmethod
    @transaction.atomic
    def update_student_report(pk, user, data):
        """
        Update student report document

        Args:
            pk: Document primary key
            user: User updating the student report
            data: Updated student report data

        Returns:
            Updated ProjectDocument instance
        """
        document = DocumentService.get_document(pk)

        if document.kind != "studentreport":
            raise ValidationError("Document is not a student report")

        settings.LOGGER.info(f"{user} is updating student report {document}")

        # Update base document
        document = DocumentService.update_document(pk, user, data)

        return document

    @staticmethod
    def get_student_report_by_year(project, year):
        """
        Get student report for project by year

        Args:
            project: Project instance
            year: Report year

        Returns:
            ProjectDocument instance or None
        """
        from ..models import ProjectDocument

        return ProjectDocument.objects.filter(
            project=project,
            kind="studentreport",
        ).first()

    @staticmethod
    def get_student_report_data(document):
        """
        Get student report specific data

        Args:
            document: ProjectDocument instance

        Returns:
            dict: Student report data
        """
        data = {
            "document": document,
            "project": document.project,
        }

        # Add student report details
        if hasattr(document, "student_report_details"):
            details = document.student_report_details.first()
            if details:
                data["details"] = details

        return data
