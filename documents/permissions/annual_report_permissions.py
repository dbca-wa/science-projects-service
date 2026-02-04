"""
Annual report permissions
"""
from rest_framework.permissions import BasePermission


class CanViewAnnualReport(BasePermission):
    """Permission to view annual report"""
    
    def has_permission(self, request, view):
        """All authenticated users can view annual reports"""
        return request.user.is_authenticated


class CanEditAnnualReport(BasePermission):
    """Permission to edit annual report"""
    
    def has_permission(self, request, view):
        """Check if user can edit annual reports"""
        # Superusers can edit
        if request.user.is_superuser:
            return True
        
        # Staff can edit
        if request.user.is_staff:
            return True
        
        return False


class CanPublishAnnualReport(BasePermission):
    """Permission to publish annual report"""
    
    def has_permission(self, request, view):
        """Check if user can publish annual reports"""
        # Superusers can publish
        if request.user.is_superuser:
            return True
        
        # Directors can publish
        if hasattr(request.user, 'director_of'):
            return request.user.director_of.exists()
        
        return False


class CanGenerateAnnualReportPDF(BasePermission):
    """Permission to generate annual report PDF"""
    
    def has_permission(self, request, view):
        """Check if user can generate annual report PDFs"""
        # Superusers can generate
        if request.user.is_superuser:
            return True
        
        # Staff can generate
        if request.user.is_staff:
            return True
        
        return False
