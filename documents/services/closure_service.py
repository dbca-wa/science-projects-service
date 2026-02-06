"""
Closure service - Project closure document operations
"""
from django.db import transaction
from django.conf import settings

from .document_service import DocumentService
from .notification_service import NotificationService


class ClosureService:
    """Business logic for project closure operations"""

    @staticmethod
    @transaction.atomic
    def create_closure(user, project, data):
        """
        Create project closure document
        
        Args:
            user: User creating the closure
            project: Project instance
            data: Closure data
            
        Returns:
            ProjectDocument instance
        """
        settings.LOGGER.info(f"{user} is creating closure for project {project}")
        
        # Create base document
        document = DocumentService.create_document(
            user=user,
            project=project,
            kind='projectclosure',
            data=data
        )
        
        # Create closure details if provided
        if data:
            # Details creation logic here
            pass
        
        return document

    @staticmethod
    @transaction.atomic
    def update_closure(pk, user, data):
        """
        Update project closure document
        
        Args:
            pk: Document primary key
            user: User updating the closure
            data: Updated closure data
            
        Returns:
            Updated ProjectDocument instance
        """
        document = DocumentService.get_document(pk)
        
        if document.kind != 'projectclosure':
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Document is not a project closure")
        
        settings.LOGGER.info(f"{user} is updating closure {document}")
        
        # Update base document
        document = DocumentService.update_document(pk, user, data)
        
        # Update closure details if provided
        if data:
            # Details update logic here
            pass
        
        return document

    @staticmethod
    @transaction.atomic
    def close_project(document, closer):
        """
        Close project using closure document
        
        Args:
            document: ProjectDocument instance (closure)
            closer: User closing the project
        """
        if document.kind != 'projectclosure':
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Document is not a project closure")
        
        if document.status != 'approved':
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Closure must be approved before closing project")
        
        settings.LOGGER.info(f"{closer} is closing project {document.project}")
        
        # Update project status
        project = document.project
        project.status = 'completed'
        project.save()
        
        # Notify project closed
        NotificationService.notify_project_closed(project, closer)

    @staticmethod
    @transaction.atomic
    def reopen_project(project, reopener):
        """
        Reopen closed project
        
        Args:
            project: Project instance
            reopener: User reopening the project
        """
        settings.LOGGER.info(f"{reopener} is reopening project {project}")
        
        # Update project status
        project.status = 'active'
        project.save()
        
        # Notify project reopened
        NotificationService.notify_project_reopened(project, reopener)

    @staticmethod
    def get_closure_data(document):
        """
        Get closure specific data
        
        Args:
            document: ProjectDocument instance
            
        Returns:
            dict: Closure data
        """
        data = {
            'document': document,
            'project': document.project,
        }
        
        # Add closure details
        if hasattr(document, 'project_closure_details'):
            details = document.project_closure_details.first()
            if details:
                data['details'] = details
        
        return data
