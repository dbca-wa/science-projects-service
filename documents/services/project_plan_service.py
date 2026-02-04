"""
Project plan service - Project plan specific operations
"""
from django.db import transaction
from django.conf import settings

from .document_service import DocumentService


class ProjectPlanService:
    """Business logic for project plan operations"""

    @staticmethod
    @transaction.atomic
    def create_project_plan(user, project, data):
        """
        Create project plan document
        
        Args:
            user: User creating the project plan
            project: Project instance
            data: Project plan data
            
        Returns:
            ProjectDocument instance
        """
        settings.LOGGER.info(f"{user} is creating project plan for project {project}")
        
        # Create base document
        document = DocumentService.create_document(
            user=user,
            project=project,
            kind='projectplan',
            data=data
        )
        
        # Create project plan details and endorsements if provided
        if data:
            # Details creation logic here
            pass
        
        return document

    @staticmethod
    @transaction.atomic
    def update_project_plan(pk, user, data):
        """
        Update project plan document
        
        Args:
            pk: Document primary key
            user: User updating the project plan
            data: Updated project plan data
            
        Returns:
            Updated ProjectDocument instance
        """
        document = DocumentService.get_document(pk)
        
        if document.kind != 'projectplan':
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Document is not a project plan")
        
        settings.LOGGER.info(f"{user} is updating project plan {document}")
        
        # Update base document
        document = DocumentService.update_document(pk, user, data)
        
        # Update project plan details and endorsements if provided
        if data:
            # Details update logic here
            pass
        
        return document

    @staticmethod
    def get_project_plan_data(document):
        """
        Get project plan specific data
        
        Args:
            document: ProjectDocument instance
            
        Returns:
            dict: Project plan data
        """
        data = {
            'document': document,
            'project': document.project,
        }
        
        # Add project plan details
        if hasattr(document, 'project_plan_details'):
            details = document.project_plan_details.first()
            if details:
                data['details'] = details
        
        # Add endorsements
        if hasattr(document, 'endorsements'):
            data['endorsements'] = document.endorsements.all()
        
        return data
