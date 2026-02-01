"""
Permission classes for caretaker operations
"""
from rest_framework.permissions import BasePermission


class CanManageCaretaker(BasePermission):
    """
    Permission to manage a caretaker relationship
    User must be admin or the caretaker themselves
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can manage this caretaker relationship
        
        Args:
            request: HTTP request
            view: View being accessed
            obj: Caretaker instance
            
        Returns:
            Boolean indicating permission
        """
        # Admins can manage any caretaker relationship
        if request.user.is_superuser:
            return True
        
        # The caretaker can manage their own relationships
        if obj.caretaker == request.user:
            return True
        
        # The user being caretaken can manage their relationships
        if obj.user == request.user:
            return True
        
        return False


class CanRespondToCaretakerRequest(BasePermission):
    """
    Permission to respond to a caretaker request
    User must be the requested caretaker
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can respond to this caretaker request
        
        Args:
            request: HTTP request
            view: View being accessed
            obj: AdminTask instance
            
        Returns:
            Boolean indicating permission
        """
        # Admins can respond to any request
        if request.user.is_superuser:
            return True
        
        # User must be in the secondary_users list (requested caretaker)
        if hasattr(obj, 'secondary_users') and request.user.pk in obj.secondary_users:
            return True
        
        return False
