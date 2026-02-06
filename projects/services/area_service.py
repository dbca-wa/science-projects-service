"""
Area service - Project area/location management
"""
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import NotFound

from ..models import ProjectArea


class AreaService:
    """Business logic for project area operations"""

    @staticmethod
    def get_project_area(project_id):
        """
        Get project area with N+1 optimization
        
        Args:
            project_id: Project ID
            
        Returns:
            ProjectArea instance
            
        Raises:
            NotFound: If area doesn't exist
        """
        try:
            return ProjectArea.objects.select_related(
                "project"
            ).get(project_id=project_id)
        except ProjectArea.DoesNotExist:
            raise NotFound(f"Project area not found for project {project_id}")

    @staticmethod
    def get_area_by_pk(pk):
        """
        Get project area by primary key
        
        Args:
            pk: ProjectArea primary key
            
        Returns:
            ProjectArea instance
            
        Raises:
            NotFound: If area doesn't exist
        """
        try:
            return ProjectArea.objects.select_related(
                "project"
            ).get(pk=pk)
        except ProjectArea.DoesNotExist:
            raise NotFound(f"Project area {pk} not found")

    @staticmethod
    @transaction.atomic
    def create_project_area(project_id, area_ids, user):
        """
        Create project area
        
        Args:
            project_id: Project ID
            area_ids: List of area IDs
            user: User creating the area
            
        Returns:
            Created ProjectArea instance
        """
        settings.LOGGER.info(f"{user} is creating areas for project {project_id}")
        
        area = ProjectArea.objects.create(
            project_id=project_id,
            areas=area_ids if area_ids else [],
        )
        
        return area

    @staticmethod
    @transaction.atomic
    def update_project_area(project_id, area_ids, user):
        """
        Update project area
        
        Args:
            project_id: Project ID
            area_ids: List of area IDs
            user: User updating the area
            
        Returns:
            Updated ProjectArea instance
        """
        area = AreaService.get_project_area(project_id)
        settings.LOGGER.info(f"{user} is updating areas for project {project_id}")
        
        area.areas = area_ids if area_ids else []
        area.save()
        
        return area

    @staticmethod
    @transaction.atomic
    def update_area_by_pk(pk, area_ids, user):
        """
        Update project area by primary key
        
        Args:
            pk: ProjectArea primary key
            area_ids: List of area IDs
            user: User updating the area
            
        Returns:
            Updated ProjectArea instance
        """
        area = AreaService.get_area_by_pk(pk)
        settings.LOGGER.info(f"{user} is updating project area {pk}")
        
        area.areas = area_ids if area_ids else []
        area.save()
        
        return area

    @staticmethod
    @transaction.atomic
    def delete_project_area(pk, user):
        """
        Delete project area
        
        Args:
            pk: ProjectArea primary key
            user: User deleting the area
        """
        area = AreaService.get_area_by_pk(pk)
        settings.LOGGER.info(f"{user} is deleting project area {pk}")
        area.delete()

    @staticmethod
    def list_all_areas():
        """List all project areas"""
        return ProjectArea.objects.all()
