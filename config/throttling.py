"""
Custom throttling classes for API rate limiting.

This module provides custom throttle classes that extend Django REST Framework's
built-in throttling to provide more granular control over API request rates.
"""

from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Throttle class for burst protection.
    
    Limits rapid successive requests to prevent abuse while allowing
    normal usage patterns. This is applied in addition to the standard
    user rate throttle.
    
    Rate: 30 requests per minute (configurable via REST_FRAMEWORK settings)
    Scope: 'burst'
    
    Example usage in a view:
        class MyView(APIView):
            throttle_classes = [BurstRateThrottle]
    """
    scope = "burst"


class LoginRateThrottle(UserRateThrottle):
    """
    Throttle class specifically for login attempts.
    
    More restrictive than general API throttling to prevent brute force attacks.
    
    Rate: 5 requests per minute (configurable via REST_FRAMEWORK settings)
    Scope: 'login'
    
    Example usage:
        class LoginView(APIView):
            throttle_classes = [LoginRateThrottle]
    """
    scope = "login"


class PasswordResetRateThrottle(UserRateThrottle):
    """
    Throttle class for password reset requests.
    
    Prevents abuse of password reset functionality.
    
    Rate: 3 requests per hour (configurable via REST_FRAMEWORK settings)
    Scope: 'password_reset'
    
    Example usage:
        class PasswordResetView(APIView):
            throttle_classes = [PasswordResetRateThrottle]
    """
    scope = "password_reset"
