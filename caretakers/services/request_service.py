"""
Business logic for caretaker request operations (AdminTask integration)
"""
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from adminoptions.models import AdminTask
from users.models import User
from ..models import Caretaker


class CaretakerRequestService:
    """Service for managing caretaker requests via AdminTask"""

    @staticmethod
    def get_pending_requests_for_user(user_id):
        """
        Get pending caretaker requests where user is being asked to be caretaker
        
        Args:
            user_id: ID of user to check
            
        Returns:
            QuerySet of AdminTask objects
        """
        return AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            secondary_users__contains=[int(user_id)],
        ).select_related(
            'primary_user',
            'primary_user__work',
            'primary_user__work__business_area',
        )

    @staticmethod
    def get_task(pk):
        """
        Get AdminTask by ID
        
        Args:
            pk: Task primary key
            
        Returns:
            AdminTask instance
            
        Raises:
            NotFound: If task doesn't exist
        """
        try:
            return AdminTask.objects.select_related(
                'primary_user',
            ).get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound(f"Task {pk} not found")

    @staticmethod
    def validate_caretaker_request(task, user):
        """
        Validate that task is a valid caretaker request for user
        
        Args:
            task: AdminTask instance
            user: User attempting to respond
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user not authorized
        """
        if task.action != AdminTask.ActionTypes.SETCARETAKER:
            raise ValidationError("This endpoint only handles caretaker requests")
        
        if task.status != AdminTask.TaskStatus.PENDING:
            raise ValidationError("This request has already been processed")
        
        if user.pk not in task.secondary_users:
            raise PermissionDenied("You are not authorized to respond to this request")

    @staticmethod
    @transaction.atomic
    def approve_request(pk, user):
        """
        Approve a caretaker request
        
        Args:
            pk: Task primary key
            user: User approving the request
            
        Returns:
            Created Caretaker instance
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user not authorized
        """
        task = CaretakerRequestService.get_task(pk)
        CaretakerRequestService.validate_caretaker_request(task, user)
        
        settings.LOGGER.info(f"{user} is approving caretaker request {task}")
        
        # Mark as approved
        task.status = AdminTask.TaskStatus.APPROVED
        task.save()
        
        try:
            # Get users
            user_who_needs_caretaker = task.primary_user
            caretaker_user = User.objects.get(pk=task.secondary_users[0])
            
            # Create caretaker relationship
            caretaker = Caretaker.objects.create(
                user=user_who_needs_caretaker,
                caretaker=caretaker_user,
                reason=task.reason,
                end_date=task.end_date,
                notes=task.notes,
            )
            
            # Mark task as fulfilled
            task.status = AdminTask.TaskStatus.FULFILLED
            task.save()
            
            return caretaker
            
        except Exception as e:
            settings.LOGGER.error(f"Error fulfilling caretaker request: {e}")
            raise ValidationError("Failed to create caretaker relationship")

    @staticmethod
    @transaction.atomic
    def reject_request(pk, user):
        """
        Reject a caretaker request
        
        Args:
            pk: Task primary key
            user: User rejecting the request
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user not authorized
        """
        task = CaretakerRequestService.get_task(pk)
        CaretakerRequestService.validate_caretaker_request(task, user)
        
        settings.LOGGER.info(f"{user} is rejecting caretaker request {task}")
        
        task.status = AdminTask.TaskStatus.REJECTED
        task.save()

    @staticmethod
    def auto_cancel_expired_request(task):
        """
        Auto-cancel an expired pending request
        
        Args:
            task: AdminTask instance
        """
        if task.end_date and task.end_date.date() < timezone.now().date():
            settings.LOGGER.info(
                f"Auto-cancelling expired caretaker request {task.id}"
            )
            task.status = AdminTask.TaskStatus.CANCELLED
            task.notes = (task.notes or "") + "\n[Auto-cancelled: end date passed while request was pending]"
            task.save()
            return True
        return False

    @staticmethod
    def get_user_requests(user):
        """
        Get caretaker requests for a user
        
        Args:
            user: User to check
            
        Returns:
            Dict with request objects
        """
        # Request where user needs a caretaker
        caretaker_request = AdminTask.objects.filter(
            primary_user=user,
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        ).first()
        
        # Request where user is being asked to be caretaker
        become_caretaker_request = AdminTask.objects.filter(
            secondary_users__contains=[user.pk],
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        ).first()
        
        # Auto-cancel expired requests
        if caretaker_request:
            if CaretakerRequestService.auto_cancel_expired_request(caretaker_request):
                caretaker_request = None
        
        if become_caretaker_request:
            if CaretakerRequestService.auto_cancel_expired_request(become_caretaker_request):
                become_caretaker_request = None
        
        return {
            'caretaker_request': caretaker_request,
            'become_caretaker_request': become_caretaker_request,
        }
