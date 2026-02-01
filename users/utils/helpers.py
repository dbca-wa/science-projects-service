"""
User helper utilities
"""
from django.db.models import Q
from django.db.models.functions import Concat
from django.db.models import Value, CharField


def search_users(queryset, search_term):
    """
    Search users by name, username, or email
    
    Args:
        queryset: Base User queryset
        search_term: Search term
        
    Returns:
        Filtered queryset
    """
    if not search_term or len(search_term) < 2:
        return queryset
    
    return queryset.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
    ).filter(
        Q(username__icontains=search_term) |
        Q(email__icontains=search_term) |
        Q(first_name__icontains=search_term) |
        Q(last_name__icontains=search_term) |
        Q(full_name__icontains=search_term)
    )


def search_profiles(queryset, search_term):
    """
    Search profiles by user name, email, or about text
    
    Args:
        queryset: Base PublicStaffProfile queryset
        search_term: Search term
        
    Returns:
        Filtered queryset
    """
    if not search_term or len(search_term) < 2:
        return queryset
    
    return queryset.filter(
        Q(user__first_name__icontains=search_term) |
        Q(user__last_name__icontains=search_term) |
        Q(user__email__icontains=search_term) |
        Q(about__icontains=search_term) |
        Q(expertise__icontains=search_term)
    )


def format_user_name(user):
    """
    Format user's full name
    
    Args:
        user: User object
        
    Returns:
        Formatted name string
    """
    return f"{user.display_first_name} {user.display_last_name}"


def get_user_avatar_url(user):
    """
    Get user's avatar URL
    
    Args:
        user: User object
        
    Returns:
        Avatar URL or None
    """
    try:
        if hasattr(user, 'avatar') and user.avatar and user.avatar.file:
            return user.avatar.file.url
    except:
        pass
    return None


def get_user_business_area(user):
    """
    Get user's business area
    
    Args:
        user: User object
        
    Returns:
        BusinessArea object or None
    """
    if hasattr(user, 'work') and user.work and user.work.business_area:
        return user.work.business_area
    return None
