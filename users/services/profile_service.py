"""
Profile service for staff profile operations
"""
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound, ValidationError

from users.models import PublicStaffProfile, UserProfile, User


class ProfileService:
    """Business logic for profile operations"""

    @staticmethod
    def list_staff_profiles(filters=None, search=None):
        """
        List staff profiles with optional filters
        
        Args:
            filters: Dict of filter parameters
            search: Search term
            
        Returns:
            QuerySet of PublicStaffProfile objects
        """
        profiles = PublicStaffProfile.objects.select_related(
            'user',
            'user__work',
            'user__work__business_area',
        ).prefetch_related(
            'employment_entries',
            'education_entries',
            'keywords',
        )
        
        if search:
            profiles = profiles.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(about__icontains=search)
            )
        
        if filters:
            if 'is_active' in filters:
                profiles = profiles.filter(is_active=filters['is_active'])
            if 'public' in filters:
                profiles = profiles.filter(public=filters['public'])
            if 'business_area' in filters:
                profiles = profiles.filter(
                    user__work__business_area_id=filters['business_area']
                )
        
        return profiles.distinct()

    @staticmethod
    def get_staff_profile(profile_id):
        """
        Get staff profile by ID
        
        Args:
            profile_id: Profile ID
            
        Returns:
            PublicStaffProfile object
            
        Raises:
            NotFound: If profile doesn't exist
        """
        try:
            return PublicStaffProfile.objects.select_related(
                'user',
                'user__work',
                'user__work__business_area',
            ).prefetch_related(
                'employment_entries',
                'education_entries',
                'keywords',
            ).get(pk=profile_id)
        except PublicStaffProfile.DoesNotExist:
            raise NotFound(f"Profile {profile_id} not found")

    @staticmethod
    def get_staff_profile_by_user(user_id):
        """
        Get staff profile by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            PublicStaffProfile object or None
        """
        try:
            return PublicStaffProfile.objects.select_related(
                'user',
                'user__work',
            ).prefetch_related(
                'employment_entries',
                'education_entries',
                'keywords',
            ).get(user_id=user_id)
        except PublicStaffProfile.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_staff_profile(user_id, data):
        """
        Create staff profile
        
        Args:
            user_id: User ID
            data: Profile data dict
            
        Returns:
            Created PublicStaffProfile object
            
        Raises:
            ValidationError: If profile already exists
        """
        if PublicStaffProfile.objects.filter(user_id=user_id).exists():
            raise ValidationError("Profile already exists for this user")
        
        settings.LOGGER.info(f"Creating staff profile for user {user_id}")
        
        profile = PublicStaffProfile.objects.create(
            user_id=user_id,
            about=data.get('about', ''),
            expertise=data.get('expertise', ''),
            public=data.get('public', False),
            is_active=data.get('is_active', True),
        )
        
        return profile

    @staticmethod
    @transaction.atomic
    def update_staff_profile(profile_id, data):
        """
        Update staff profile
        
        Args:
            profile_id: Profile ID
            data: Update data dict
            
        Returns:
            Updated PublicStaffProfile object
        """
        profile = ProfileService.get_staff_profile(profile_id)
        settings.LOGGER.info(f"Updating staff profile {profile_id}")
        
        for field, value in data.items():
            setattr(profile, field, value)
        
        profile.save()
        return profile

    @staticmethod
    @transaction.atomic
    def delete_staff_profile(profile_id):
        """
        Delete staff profile
        
        Args:
            profile_id: Profile ID
        """
        profile = ProfileService.get_staff_profile(profile_id)
        settings.LOGGER.info(f"Deleting staff profile {profile_id}")
        profile.delete()

    @staticmethod
    @transaction.atomic
    def toggle_visibility(profile_id):
        """
        Toggle profile public visibility
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Updated PublicStaffProfile object
        """
        profile = ProfileService.get_staff_profile(profile_id)
        profile.public = not profile.public
        profile.save()
        
        settings.LOGGER.info(f"Toggled visibility for profile {profile_id}: {profile.public}")
        return profile

    @staticmethod
    def get_active_staff_emails():
        """
        Get all active staff profile emails
        
        Returns:
            QuerySet of PublicStaffProfile objects
        """
        return PublicStaffProfile.objects.filter(
            is_active=True,
            user__is_active=True,
        ).select_related('user')

    @staticmethod
    def check_staff_profile_exists(user_id):
        """
        Check if staff profile exists and return data
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with profile data and active state
        """
        try:
            profile = PublicStaffProfile.objects.select_related('user').get(user_id=user_id)
            return {
                'exists': True,
                'is_active': profile.is_active,
                'profile': profile,
            }
        except PublicStaffProfile.DoesNotExist:
            return {
                'exists': False,
                'is_active': False,
                'profile': None,
            }

    @staticmethod
    def list_user_profiles(filters=None):
        """
        List user profiles
        
        Args:
            filters: Dict of filter parameters
            
        Returns:
            QuerySet of UserProfile objects
        """
        profiles = UserProfile.objects.select_related('user')
        
        if filters:
            if 'user' in filters:
                profiles = profiles.filter(user_id=filters['user'])
        
        return profiles

    @staticmethod
    def get_user_profile(profile_id):
        """
        Get user profile by ID
        
        Args:
            profile_id: Profile ID
            
        Returns:
            UserProfile object
            
        Raises:
            NotFound: If profile doesn't exist
        """
        try:
            return UserProfile.objects.select_related('user').get(pk=profile_id)
        except UserProfile.DoesNotExist:
            raise NotFound(f"User profile {profile_id} not found")

    @staticmethod
    @transaction.atomic
    def update_user_profile(profile_id, data):
        """
        Update user profile
        
        Args:
            profile_id: Profile ID
            data: Update data dict
            
        Returns:
            Updated UserProfile object
        """
        profile = ProfileService.get_user_profile(profile_id)
        settings.LOGGER.info(f"Updating user profile {profile_id}")
        
        for field, value in data.items():
            setattr(profile, field, value)
        
        profile.save()
        return profile

    @staticmethod
    @transaction.atomic
    def update_personal_information(user_id, data):
        """
        Update user personal information
        
        Args:
            user_id: User ID
            data: Update data dict
            
        Returns:
            Updated User object
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise NotFound(f"User {user_id} not found")
        
        settings.LOGGER.info(f"Updating personal information for user {user_id}")
        
        for field, value in data.items():
            setattr(user, field, value)
        
        user.save()
        return user
