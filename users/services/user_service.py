"""
User service for core user operations
"""
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Q, Case, When, Value, CharField
from django.db.models.functions import Concat
from rest_framework.exceptions import NotFound, ValidationError

from users.models import User, UserWork


class UserService:
    """Business logic for user operations"""

    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate user with username and password
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User object if authenticated, None otherwise
        """
        if not username or not password:
            raise ValidationError("Username and password are required")
        
        return authenticate(username=username, password=password)

    @staticmethod
    def login_user(request, user):
        """
        Log in user
        
        Args:
            request: HTTP request
            user: User to log in
        """
        login(request, user)

    @staticmethod
    def logout_user(request):
        """
        Log out user
        
        Args:
            request: HTTP request
            
        Returns:
            Dict with logout URL if available
        """
        settings.LOGGER.info(f"{request.user} is logging out")
        logout(request)
        
        logout_url = request.META.get("HTTP_X_LOGOUT_URL")
        if logout_url:
            return {"logoutUrl": logout_url}
        return {}

    @staticmethod
    @transaction.atomic
    def change_password(user, old_password, new_password):
        """
        Change user password
        
        Args:
            user: User object
            old_password: Current password
            new_password: New password
            
        Raises:
            ValidationError: If old password is incorrect
        """
        if not user.check_password(old_password):
            raise ValidationError("Incorrect old password")
        
        user.set_password(new_password)
        user.save()

    @staticmethod
    def list_users(filters=None, search=None):
        """
        List users with optional filters
        
        Args:
            filters: Dict of filter parameters
            search: Search term
            
        Returns:
            QuerySet of User objects
        """
        users = User.objects.select_related(
            'profile',
            'work',
            'work__business_area',
        ).prefetch_related(
            'groups',
        )
        
        if search:
            users = users.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(full_name__icontains=search)
            )
        
        if filters:
            if 'is_active' in filters:
                users = users.filter(is_active=filters['is_active'])
            if 'is_staff' in filters:
                users = users.filter(is_staff=filters['is_staff'])
            if 'is_superuser' in filters:
                users = users.filter(is_superuser=filters['is_superuser'])
            if 'business_area' in filters:
                users = users.filter(work__business_area_id=filters['business_area'])
        
        return users.distinct()

    @staticmethod
    def get_user(user_id):
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            NotFound: If user doesn't exist
        """
        try:
            return User.objects.select_related(
                'profile',
                'work',
                'work__business_area',
            ).prefetch_related(
                'groups',
            ).get(pk=user_id)
        except User.DoesNotExist:
            raise NotFound(f"User {user_id} not found")

    @staticmethod
    @transaction.atomic
    def create_user(data):
        """
        Create new user
        
        Args:
            data: User data dict
            
        Returns:
            Created User object
        """
        settings.LOGGER.info(f"Creating user: {data.get('username')}")
        
        user = User.objects.create_user(
            username=data['username'],
            email=data.get('email', ''),
            password=data.get('password', User.objects.make_random_password()),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_staff=data.get('is_staff', False),
            is_superuser=data.get('is_superuser', False),
        )
        
        return user

    @staticmethod
    @transaction.atomic
    def update_user(user_id, data):
        """
        Update user
        
        Args:
            user_id: User ID
            data: Update data dict
            
        Returns:
            Updated User object
        """
        user = UserService.get_user(user_id)
        settings.LOGGER.info(f"Updating user {user}")
        
        for field, value in data.items():
            if field == 'password':
                user.set_password(value)
            else:
                setattr(user, field, value)
        
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(user_id):
        """
        Delete user
        
        Args:
            user_id: User ID
        """
        user = UserService.get_user(user_id)
        settings.LOGGER.info(f"Deleting user {user}")
        user.delete()

    @staticmethod
    @transaction.atomic
    def toggle_active(user_id):
        """
        Toggle user active status
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User object
        """
        user = UserService.get_user(user_id)
        user.is_active = not user.is_active
        user.save()
        
        settings.LOGGER.info(f"Toggled active status for {user}: {user.is_active}")
        return user

    @staticmethod
    @transaction.atomic
    def switch_admin(user_id):
        """
        Toggle user admin status
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User object
        """
        user = UserService.get_user(user_id)
        user.is_superuser = not user.is_superuser
        user.save()
        
        settings.LOGGER.info(f"Toggled admin status for {user}: {user.is_superuser}")
        return user

    @staticmethod
    def check_email_exists(email):
        """
        Check if email already exists
        
        Args:
            email: Email to check
            
        Returns:
            Boolean
        """
        return User.objects.filter(email=email).exists()

    @staticmethod
    def check_username_exists(username):
        """
        Check if username already exists
        
        Args:
            username: Username to check
            
        Returns:
            Boolean
        """
        return User.objects.filter(username=username).exists()

    @staticmethod
    def get_users_by_directorate(directorate_id):
        """
        Get users by directorate
        
        Args:
            directorate_id: Directorate ID
            
        Returns:
            QuerySet of User objects
        """
        return User.objects.filter(
            work__business_area__division__directorate_id=directorate_id
        ).select_related(
            'work',
            'work__business_area',
            'work__business_area__division',
            'work__business_area__division__directorate',
        ).distinct()
