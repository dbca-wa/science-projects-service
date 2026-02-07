"""
Base permission classes for common authorization patterns
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Permission to check if user is admin/superuser

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, IsAdminUser]
    """

    def has_permission(self, request, view):
        """
        Check if user is admin

        Args:
            request: HTTP request
            view: View being accessed

        Returns:
            Boolean indicating if user is admin
        """
        return request.user and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        """
        Check if user is admin for object-level permission

        Args:
            request: HTTP request
            view: View being accessed
            obj: Object being accessed

        Returns:
            Boolean indicating if user is admin
        """
        return request.user and request.user.is_superuser


class IsOwnerOrAdmin(BasePermission):
    """
    Permission to check if user is owner of object or admin

    Object must have a 'user' or 'owner' attribute

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is owner or admin

        Args:
            request: HTTP request
            view: View being accessed
            obj: Object being accessed (must have user/owner attribute)

        Returns:
            Boolean indicating if user is owner or admin
        """
        # Admins can access anything
        if request.user.is_superuser:
            return True

        # Check if user is owner
        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "owner"):
            return obj.owner == request.user

        # If no user/owner attribute, deny access
        return False
