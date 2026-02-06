"""
Business logic for caretaker request operations (via AdminTask)
"""
from datetime import datetime
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from adminoptions.models import AdminTask
from ..models import Caretaker
from users.models import User


class CaretakerRequestService:
    """Service for managing caretaker requests via AdminTask"""

    @staticmethod
    def get_task(task_id):
        """
        Get a caretaker request task by ID
        
        Args:
            task_id: AdminTask ID
            
        Returns:
            AdminTask instance
            
        Raises:
            NotFound: If task not found
        """
        try:
            return AdminTask.objects.select_related(
                'requester',
                'primary_user',
            ).get(
                pk=task_id,
                action=AdminTask.ActionTypes.SETCARETAKER,
            )
        except AdminTask.DoesNotExist:
            raise NotFound(f"Task {task_id} not found")

    @staticmethod
    def validate_caretaker_request(task, user):
        """
        Validate a caretaker request before processing
        
        Args:
            task: AdminTask instance
            user: User attempting to process the request
            
        Raises:
            ValidationError: If task is invalid
            PermissionDenied: If user lacks permission
        """
        # Validate action type
        if task.action != AdminTask.ActionTypes.SETCARETAKER:
            raise ValidationError("This endpoint only handles caretaker requests")
        
        # Validate status
        if task.status != AdminTask.TaskStatus.PENDING:
            raise ValidationError("This request has already been processed")
        
        # Validate user is the requested caretaker (in secondary_users)
        caretaker_id = task.secondary_users[0] if task.secondary_users else None
        if not (user.is_superuser or user.pk == caretaker_id):
            raise PermissionDenied("You are not authorized to respond to this request")

    @staticmethod
    @transaction.atomic
    def auto_cancel_expired_request(task):
        """
        Auto-cancel a caretaker request if it has expired
        
        Args:
            task: AdminTask instance
            
        Returns:
            bool: True if cancelled, False if not expired
        """
        # Only cancel if task has end_date and it's in the past
        if not task.end_date:
            return False
        
        # Convert end_date to date if it's a datetime
        end_date = task.end_date
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        if end_date >= timezone.now().date():
            return False
        
        # Cancel the task
        task.status = AdminTask.TaskStatus.CANCELLED
        task.notes = f"Auto-cancelled: Request expired on {end_date}"
        task.save()
        
        settings.LOGGER.info(
            f"Auto-cancelled expired caretaker request {task.pk}"
        )
        
        return True

    @staticmethod
    def get_user_requests(user):
        """
        Get caretaker requests for a user
        
        Returns both:
        - caretaker_request: Request where user is primary_user (wants someone to be THEIR caretaker)
        - become_caretaker_request: Request where user is in secondary_users (someone wants THEM to be caretaker)
        
        Auto-cancels any expired requests.
        
        Args:
            user: User instance
            
        Returns:
            dict with 'caretaker_request' and 'become_caretaker_request' keys
        """
        # Get caretaker request (user wants someone to be their caretaker)
        caretaker_request = AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
        ).select_related(
            'requester',
            'primary_user',
        ).first()
        
        # Auto-cancel if expired
        if caretaker_request:
            cancelled = CaretakerRequestService.auto_cancel_expired_request(caretaker_request)
            if cancelled:
                caretaker_request = None
        
        # Get become caretaker request (someone wants user to be their caretaker)
        become_caretaker_request = AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            secondary_users__contains=[user.pk],
        ).select_related(
            'requester',
            'primary_user',
        ).first()
        
        # Auto-cancel if expired
        if become_caretaker_request:
            cancelled = CaretakerRequestService.auto_cancel_expired_request(become_caretaker_request)
            if cancelled:
                become_caretaker_request = None
        
        return {
            'caretaker_request': caretaker_request,
            'become_caretaker_request': become_caretaker_request,
        }

    @staticmethod
    @transaction.atomic
    def create_request(requester, user_id, caretaker_id, reason=None, end_date=None, notes=None):
        """
        Create a new caretaker request (AdminTask)
        
        Args:
            requester: User creating the request
            user_id: ID of user to be caretaken for
            caretaker_id: ID of user to become caretaker
            reason: Optional reason
            end_date: Optional end date
            notes: Optional notes
            
        Returns:
            AdminTask instance
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user lacks permission
        """
        # Validate users exist
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({"user_id": "User not found"})
        
        try:
            caretaker = User.objects.get(pk=caretaker_id)
        except User.DoesNotExist:
            raise ValidationError({"caretaker_id": "Caretaker not found"})
        
        # Validate not self-caretaking
        if user_id == caretaker_id:
            raise ValidationError("Cannot caretake for yourself")
        
        # Validate no duplicate pending request
        existing = AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            primary_user=user,
            status=AdminTask.TaskStatus.PENDING,
        ).exists()
        
        if existing:
            raise ValidationError("User already has a pending caretaker request")
        
        # Validate no existing caretaker
        if Caretaker.objects.filter(user=user, caretaker=caretaker).exists():
            raise ValidationError("User already has this caretaker")
        
        # Validate end_date not in past
        if end_date:
            if isinstance(end_date, str):
                try:
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
                except (ValueError, AttributeError) as e:
                    raise ValidationError({"end_date": f"Invalid date format: {e}"})
            
            if end_date < timezone.now().date():
                raise ValidationError({"end_date": "End date cannot be in the past"})
        
        # Create AdminTask
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            requester=requester,
            primary_user=user,
            secondary_users=[caretaker_id],
            reason=reason,
            end_date=end_date,
            notes=notes,
        )
        
        settings.LOGGER.info(
            f"{requester} created caretaker request {task.id}: {caretaker} for {user}"
        )
        
        return task

    @staticmethod
    def get_pending_requests_for_user(user_id):
        """
        Get all pending caretaker requests where user is in secondary_users
        (people who want THIS user to be THEIR caretaker)
        
        Args:
            user_id: User ID
            
        Returns:
            QuerySet of AdminTask objects
        """
        return AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            secondary_users__contains=[int(user_id)],
        ).select_related(
            'requester',
            'primary_user',
        ).order_by('-created_at')

    @staticmethod
    def get_outgoing_requests_for_user(user_id):
        """
        Get all pending caretaker requests where user is primary_user
        (requests THIS user made for someone to be THEIR caretaker)
        
        Args:
            user_id: User ID
            
        Returns:
            QuerySet of AdminTask objects
        """
        return AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user_id=user_id,
        ).select_related(
            'requester',
            'primary_user',
        ).order_by('-created_at')

    @staticmethod
    @transaction.atomic
    def approve_request(task_id, approver):
        """
        Approve a caretaker request
        
        Args:
            task_id: AdminTask ID
            approver: User approving the request
            
        Returns:
            Caretaker instance
            
        Raises:
            NotFound: If task not found
            PermissionDenied: If user lacks permission
            ValidationError: If task invalid or caretaker creation fails
        """
        # Get task
        try:
            task = AdminTask.objects.select_related(
                'primary_user',
            ).get(
                pk=task_id,
                action=AdminTask.ActionTypes.SETCARETAKER,
            )
        except AdminTask.DoesNotExist:
            raise NotFound(f"Caretaker request {task_id} not found")
        
        # Validate status
        if task.status != AdminTask.TaskStatus.PENDING:
            raise ValidationError(f"Request is already {task.status}")
        
        # Check permission (admin OR caretaker being requested)
        # The caretaker (in secondary_users) must approve, not the requester
        caretaker_id = task.secondary_users[0] if task.secondary_users else None
        
        # Validate that secondary_users is not empty
        if not caretaker_id:
            raise ValidationError("Cannot approve request: no caretaker specified in secondary_users")
        
        if not (approver.is_superuser or approver.pk == caretaker_id):
            raise PermissionDenied("Only the requested caretaker or an admin can approve this request")
        
        # Get caretaker user (safe now - we validated caretaker_id exists)
        caretaker = User.objects.get(pk=caretaker_id)
        
        # Create Caretaker relationship
        try:
            caretaker_obj = Caretaker.objects.create(
                user=task.primary_user,
                caretaker=caretaker,
                reason=task.reason,
                end_date=task.end_date,
                notes=task.notes,
            )
        except Exception as e:
            raise ValidationError(f"Failed to create caretaker relationship: {e}")
        
        # Update task status to FULFILLED (request approved AND caretaker created)
        task.status = AdminTask.TaskStatus.FULFILLED
        task.save()
        
        settings.LOGGER.info(
            f"{approver} approved caretaker request {task_id}: "
            f"{caretaker} for {task.primary_user}"
        )
        
        return caretaker_obj

    @staticmethod
    @transaction.atomic
    def reject_request(task_id, rejector):
        """
        Reject a caretaker request
        
        Args:
            task_id: AdminTask ID
            rejector: User rejecting the request
            
        Raises:
            NotFound: If task not found
            PermissionDenied: If user lacks permission
            ValidationError: If task invalid
        """
        # Get task
        try:
            task = AdminTask.objects.select_related(
                'primary_user',
            ).get(
                pk=task_id,
                action=AdminTask.ActionTypes.SETCARETAKER,
            )
        except AdminTask.DoesNotExist:
            raise NotFound(f"Caretaker request {task_id} not found")
        
        # Validate status
        if task.status != AdminTask.TaskStatus.PENDING:
            raise ValidationError(f"Request is already {task.status}")
        
        # Check permission (admin OR caretaker being requested)
        # The caretaker (in secondary_users) must reject, not the requester
        caretaker_id = task.secondary_users[0] if task.secondary_users else None
        if not (rejector.is_superuser or rejector.pk == caretaker_id):
            raise PermissionDenied("Only the requested caretaker or an admin can reject this request")
        
        # Update task status
        task.status = AdminTask.TaskStatus.REJECTED
        task.save()
        
        settings.LOGGER.info(
            f"{rejector} rejected caretaker request {task_id}"
        )

    @staticmethod
    @transaction.atomic
    def cancel_request(task_id, canceller):
        """
        Cancel a caretaker request
        
        Args:
            task_id: AdminTask ID
            canceller: User cancelling the request
            
        Raises:
            NotFound: If task not found
            PermissionDenied: If user lacks permission
            ValidationError: If task invalid
        """
        # Get task
        try:
            task = AdminTask.objects.select_related(
                'requester',
                'primary_user',
            ).get(
                pk=task_id,
                action=AdminTask.ActionTypes.SETCARETAKER,
            )
        except AdminTask.DoesNotExist:
            raise NotFound(f"Caretaker request {task_id} not found")
        
        # Validate status
        if task.status != AdminTask.TaskStatus.PENDING:
            raise ValidationError(f"Request is already {task.status}")
        
        # Check permission (admin OR requester)
        if not (canceller.is_superuser or canceller.pk == task.requester.pk):
            raise PermissionDenied("You don't have permission to cancel this request")
        
        # Update task status
        task.status = AdminTask.TaskStatus.CANCELLED
        task.save()
        
        settings.LOGGER.info(
            f"{canceller} cancelled caretaker request {task_id}"
        )
