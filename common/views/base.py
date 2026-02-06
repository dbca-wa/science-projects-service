"""
Base view classes for consistent API structure
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class BaseAPIView(APIView):
    """
    Base API view with common configuration
    
    All views should inherit from this to ensure consistent behavior:
    - Authentication required by default
    - Standard error handling
    - Consistent response formatting
    """
    permission_classes = [IsAuthenticated]
    
    def handle_exception(self, exc):
        """
        Handle exceptions consistently across all views
        
        Args:
            exc: Exception that was raised
            
        Returns:
            Response with appropriate error format
        """
        # Let DRF handle the exception with standard formatting
        return super().handle_exception(exc)
