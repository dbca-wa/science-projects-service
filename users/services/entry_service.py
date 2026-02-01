"""
Entry service for employment and education entries
"""
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound

from users.models import EmploymentEntry, EducationEntry


class EmploymentService:
    """Business logic for employment entry operations"""

    @staticmethod
    def list_employment(profile_id):
        """
        List employment entries for profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            QuerySet of EmploymentEntry objects
        """
        return EmploymentEntry.objects.filter(
            profile_id=profile_id
        ).order_by('-start_year', '-end_year')

    @staticmethod
    def get_employment(entry_id):
        """
        Get employment entry by ID
        
        Args:
            entry_id: Entry ID
            
        Returns:
            EmploymentEntry object
            
        Raises:
            NotFound: If entry doesn't exist
        """
        try:
            return EmploymentEntry.objects.get(pk=entry_id)
        except EmploymentEntry.DoesNotExist:
            raise NotFound(f"Employment entry {entry_id} not found")

    @staticmethod
    @transaction.atomic
    def create_employment(profile_id, data):
        """
        Create employment entry
        
        Args:
            profile_id: Profile ID
            data: Entry data dict
            
        Returns:
            Created EmploymentEntry object
        """
        settings.LOGGER.info(f"Creating employment entry for profile {profile_id}")
        
        entry = EmploymentEntry.objects.create(
            profile_id=profile_id,
            position=data['position'],
            organisation=data['organisation'],
            start_year=data['start_year'],
            end_year=data.get('end_year'),
        )
        
        return entry

    @staticmethod
    @transaction.atomic
    def update_employment(entry_id, data):
        """
        Update employment entry
        
        Args:
            entry_id: Entry ID
            data: Update data dict
            
        Returns:
            Updated EmploymentEntry object
        """
        entry = EmploymentService.get_employment(entry_id)
        settings.LOGGER.info(f"Updating employment entry {entry_id}")
        
        for field, value in data.items():
            setattr(entry, field, value)
        
        entry.save()
        return entry

    @staticmethod
    @transaction.atomic
    def delete_employment(entry_id):
        """
        Delete employment entry
        
        Args:
            entry_id: Entry ID
        """
        entry = EmploymentService.get_employment(entry_id)
        settings.LOGGER.info(f"Deleting employment entry {entry_id}")
        entry.delete()


class EducationService:
    """Business logic for education entry operations"""

    @staticmethod
    def list_education(profile_id):
        """
        List education entries for profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            QuerySet of EducationEntry objects
        """
        return EducationEntry.objects.filter(
            profile_id=profile_id
        ).order_by('-year')

    @staticmethod
    def get_education(entry_id):
        """
        Get education entry by ID
        
        Args:
            entry_id: Entry ID
            
        Returns:
            EducationEntry object
            
        Raises:
            NotFound: If entry doesn't exist
        """
        try:
            return EducationEntry.objects.get(pk=entry_id)
        except EducationEntry.DoesNotExist:
            raise NotFound(f"Education entry {entry_id} not found")

    @staticmethod
    @transaction.atomic
    def create_education(profile_id, data):
        """
        Create education entry
        
        Args:
            profile_id: Profile ID
            data: Entry data dict
            
        Returns:
            Created EducationEntry object
        """
        settings.LOGGER.info(f"Creating education entry for profile {profile_id}")
        
        entry = EducationEntry.objects.create(
            profile_id=profile_id,
            qualification=data['qualification'],
            institution=data['institution'],
            year=data['year'],
        )
        
        return entry

    @staticmethod
    @transaction.atomic
    def update_education(entry_id, data):
        """
        Update education entry
        
        Args:
            entry_id: Entry ID
            data: Update data dict
            
        Returns:
            Updated EducationEntry object
        """
        entry = EducationService.get_education(entry_id)
        settings.LOGGER.info(f"Updating education entry {entry_id}")
        
        for field, value in data.items():
            setattr(entry, field, value)
        
        entry.save()
        return entry

    @staticmethod
    @transaction.atomic
    def delete_education(entry_id):
        """
        Delete education entry
        
        Args:
            entry_id: Entry ID
        """
        entry = EducationService.get_education(entry_id)
        settings.LOGGER.info(f"Deleting education entry {entry_id}")
        entry.delete()
