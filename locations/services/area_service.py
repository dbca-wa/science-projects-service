"""
Area service - Business logic for area operations
"""

from django.conf import settings
from rest_framework.exceptions import NotFound

from locations.models import Area


class AreaService:
    """Business logic for area operations"""

    @staticmethod
    def list_areas(area_type=None):
        """
        List all areas, optionally filtered by type

        Args:
            area_type: Optional area type filter

        Returns:
            QuerySet of Area objects
        """
        queryset = Area.objects.all()
        if area_type:
            queryset = queryset.filter(area_type=area_type)
        return queryset

    @staticmethod
    def get_area(pk):
        """
        Get area by ID

        Args:
            pk: Area primary key

        Returns:
            Area instance

        Raises:
            NotFound: If area doesn't exist
        """
        try:
            return Area.objects.get(pk=pk)
        except Area.DoesNotExist:
            raise NotFound(f"Area {pk} not found")

    @staticmethod
    def create_area(user, data):
        """
        Create new area

        Args:
            user: User creating the area
            data: Validated area data

        Returns:
            Created Area instance
        """
        settings.LOGGER.info(f"{user} is creating area")
        return Area.objects.create(**data)

    @staticmethod
    def update_area(pk, user, data):
        """
        Update area

        Args:
            pk: Area primary key
            user: User updating the area
            data: Validated area data

        Returns:
            Updated Area instance
        """
        area = AreaService.get_area(pk)
        settings.LOGGER.info(f"{user} is updating area {area}")

        for field, value in data.items():
            setattr(area, field, value)
        area.save()

        return area

    @staticmethod
    def delete_area(pk, user):
        """
        Delete area

        Args:
            pk: Area primary key
            user: User deleting the area
        """
        area = AreaService.get_area(pk)
        settings.LOGGER.info(f"{user} is deleting area {area}")
        area.delete()
