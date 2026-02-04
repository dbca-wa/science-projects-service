"""
Business logic for caretaker relationship operations
"""
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError

from ..models import Caretaker
from users.models import User


class CaretakerService:
    """Service for managing caretaker relationships"""

    @staticmethod
    def list_caretakers():
        """
        List all caretaker relationships
        
        Returns:
            QuerySet of Caretaker objects
        """
        return Caretaker.objects.select_related(
            'user',
            'user__work',
            'user__work__business_area',
            'caretaker',
            'caretaker__work',
            'caretaker__work__business_area',
        ).prefetch_related(
            'user__business_areas_led',
            'caretaker__business_areas_led',
        )

    @staticmethod
    def get_caretaker(pk):
        """
        Get caretaker relationship by ID
        
        Args:
            pk: Caretaker primary key
            
        Returns:
            Caretaker instance
            
        Raises:
            NotFound: If caretaker doesn't exist
        """
        try:
            return Caretaker.objects.select_related(
                'user',
                'caretaker',
            ).get(pk=pk)
        except Caretaker.DoesNotExist:
            raise NotFound(f"Caretaker {pk} not found")

    @staticmethod
    @transaction.atomic
    def create_caretaker(user, caretaker, reason, end_date=None, notes=None):
        """
        Create a new caretaker relationship
        
        Args:
            user: User being caretaken for
            caretaker: User acting as caretaker
            reason: Reason for caretaker relationship
            end_date: Optional end date
            notes: Optional notes
            
        Returns:
            Created Caretaker instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate users exist
        if not isinstance(user, User):
            try:
                user = User.objects.get(pk=user)
            except User.DoesNotExist:
                raise ValidationError({"user": "User not found"})
        
        if not isinstance(caretaker, User):
            try:
                caretaker = User.objects.get(pk=caretaker)
            except User.DoesNotExist:
                raise ValidationError({"caretaker": "Caretaker not found"})
        
        # Validate not self-caretaking
        if user == caretaker:
            raise ValidationError("Cannot caretake for yourself")
        
        # Check for existing relationship
        if Caretaker.objects.filter(user=user, caretaker=caretaker).exists():
            raise ValidationError("Caretaker relationship already exists")
        
        # Reject if caretaker has a caretaker
        if caretaker.caretakers.exists():
            raise ValidationError("Cannot set a user with a caretaker as caretaker")
        
        settings.LOGGER.info(f"Creating caretaker relationship: {caretaker} for {user}")
        
        return Caretaker.objects.create(
            user=user,
            caretaker=caretaker,
            reason=reason,
            end_date=end_date,
            notes=notes,
        )

    @staticmethod
    @transaction.atomic
    def update_caretaker(pk, data):
        """
        Update caretaker relationship
        
        Args:
            pk: Caretaker primary key
            data: Dict of fields to update
            
        Returns:
            Updated Caretaker instance
        """
        caretaker = CaretakerService.get_caretaker(pk)
        
        settings.LOGGER.info(f"Updating caretaker {caretaker}")
        
        for field, value in data.items():
            if hasattr(caretaker, field):
                setattr(caretaker, field, value)
        
        caretaker.save()
        return caretaker

    @staticmethod
    @transaction.atomic
    def delete_caretaker(pk, user):
        """
        Delete caretaker relationship
        
        Args:
            pk: Caretaker primary key
            user: User performing deletion (for logging)
        """
        caretaker = CaretakerService.get_caretaker(pk)
        
        settings.LOGGER.info(f"{user} is deleting caretaker {caretaker}")
        
        caretaker.delete()

    @staticmethod
    def get_user_caretaker(user):
        """
        Get caretaker object for a user
        
        Args:
            user: User to check
            
        Returns:
            Caretaker instance or None
        """
        caretaker_qs = Caretaker.objects.filter(user=user).select_related(
            'caretaker',
            'caretaker__work',
            'caretaker__work__business_area',
        )
        
        return caretaker_qs.first() if caretaker_qs.exists() else None

    @staticmethod
    def get_caretaker_check(user):
        """
        Check caretaker status for user
        Returns active caretaker, pending requests
        
        Maintains same format as legacy for frontend compatibility
        
        Args:
            user: User to check
            
        Returns:
            Dict with three keys:
                - caretaker_object: Active Caretaker where user is being caretaken for
                - caretaker_request_object: Pending AdminTask where user is primary_user
                - become_caretaker_request_object: Pending AdminTask where user is in secondary_users
        """
        from adminoptions.models import AdminTask
        
        # Active caretaker
        caretaker_object = Caretaker.objects.filter(user=user).select_related(
            'caretaker',
            'caretaker__work',
            'caretaker__work__business_area',
        ).first()
        
        # Pending request where user is primary_user
        caretaker_request_object = AdminTask.objects.filter(
            primary_user=user,
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        ).select_related('requester').first()
        
        # Pending request where user is in secondary_users
        become_caretaker_request_object = AdminTask.objects.filter(
            secondary_users__contains=[user.pk],
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        ).select_related('requester', 'primary_user').first()
        
        return {
            'caretaker_object': caretaker_object,
            'caretaker_request_object': caretaker_request_object,
            'become_caretaker_request_object': become_caretaker_request_object,
        }
