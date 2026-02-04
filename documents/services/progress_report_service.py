"""
Progress report service - Progress report specific operations
"""
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError

from .document_service import DocumentService


class ProgressReportService:
    """Business logic for progress report operations"""

    @staticmethod
    @transaction.atomic
    def create_progress_report(user, project, year, data):
        """
        Create progress report document
        
        Args:
            user: User creating the progress report
            project: Project instance
            year: Report year
            data: Progress report data
            
        Returns:
            ProjectDocument instance
        """
        settings.LOGGER.info(f"{user} is creating progress report for project {project} year {year}")
        
        # Create base document
        document = DocumentService.create_document(
            user=user,
            project=project,
            kind='progressreport',
            data=data
        )
        
        return document

    @staticmethod
    @transaction.atomic
    def update_progress_report(pk, user, data):
        """
        Update progress report document
        
        Args:
            pk: Document primary key
            user: User updating the progress report
            data: Updated progress report data
            
        Returns:
            Updated ProjectDocument instance
        """
        document = DocumentService.get_document(pk)
        
        if document.kind != 'progressreport':
            raise ValidationError("Document is not a progress report")
        
        settings.LOGGER.info(f"{user} is updating progress report {document}")
        
        # Update base document
        document = DocumentService.update_document(pk, user, data)
        
        return document

    @staticmethod
    def get_progress_report_by_year(project, year):
        """
        Get progress report for project by year
        
        Args:
            project: Project instance
            year: Report year
            
        Returns:
            ProjectDocument instance or None
        """
        from ..models import ProjectDocument
        
        return ProjectDocument.objects.filter(
            project=project,
            kind='progressreport',
        ).first()

    @staticmethod
    def get_progress_report_data(document):
        """
        Get progress report specific data
        
        Args:
            document: ProjectDocument instance
            
        Returns:
            dict: Progress report data
        """
        data = {
            'document': document,
            'project': document.project,
        }
        
        # Add progress report details
        if hasattr(document, 'progress_report_details'):
            details = document.progress_report_details.first()
            if details:
                data['details'] = details
        
        return data
