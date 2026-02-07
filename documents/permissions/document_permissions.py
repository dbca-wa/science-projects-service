"""
Document permissions
"""

from rest_framework.permissions import BasePermission


class CanViewDocument(BasePermission):
    """Permission to view document"""

    def has_object_permission(self, request, view, obj):
        """Check if user can view document"""
        # Superusers can view all
        if request.user.is_superuser:
            return True

        # Project members can view
        if obj.project.members.filter(user=request.user).exists():
            return True

        # Business area leader can view
        if obj.project.business_area.leader == request.user:
            return True

        # Director can view
        if (
            obj.project.business_area.division
            and obj.project.business_area.division.director == request.user
        ):
            return True

        return False


class CanEditDocument(BasePermission):
    """Permission to edit document"""

    def has_object_permission(self, request, view, obj):
        """Check if user can edit document"""
        # Superusers can edit all
        if request.user.is_superuser:
            return True

        # Cannot edit approved documents
        if obj.status == "approved":
            return False

        # Project members can edit
        if obj.project.members.filter(user=request.user).exists():
            return True

        return False


class CanApproveDocument(BasePermission):
    """Permission to approve document"""

    def has_object_permission(self, request, view, obj):
        """Check if user can approve document"""
        # Superusers can approve all
        if request.user.is_superuser:
            return True

        # Document must be in approval status
        if obj.status != "inapproval":
            return False

        # Check approval stage
        if not obj.project_lead_approval_granted:
            # Stage 1: Project lead
            return obj.project.members.filter(
                user=request.user, is_leader=True
            ).exists()

        elif not obj.business_area_lead_approval_granted:
            # Stage 2: Business area leader
            return obj.project.business_area.leader == request.user

        elif not obj.directorate_approval_granted:
            # Stage 3: Director
            if obj.project.business_area.division:
                return obj.project.business_area.division.director == request.user

        return False


class CanRecallDocument(BasePermission):
    """Permission to recall document"""

    def has_object_permission(self, request, view, obj):
        """Check if user can recall document"""
        # Superusers can recall all
        if request.user.is_superuser:
            return True

        # Document must be in approval
        if obj.status != "inapproval":
            return False

        # Project lead can recall
        if obj.project.members.filter(user=request.user, is_leader=True).exists():
            return True

        return False


class CanDeleteDocument(BasePermission):
    """Permission to delete document"""

    def has_object_permission(self, request, view, obj):
        """Check if user can delete document"""
        # Superusers can delete all
        if request.user.is_superuser:
            return True

        # Cannot delete approved documents
        if obj.status == "approved":
            return False

        # Project lead can delete
        if obj.project.members.filter(user=request.user, is_leader=True).exists():
            return True

        return False


class CanGeneratePDF(BasePermission):
    """Permission to generate PDF"""

    def has_object_permission(self, request, view, obj):
        """Check if user can generate PDF"""
        # Superusers can generate all
        if request.user.is_superuser:
            return True

        # Document must be approved
        if obj.status != "approved":
            return False

        # Project members can generate
        if obj.project.members.filter(user=request.user).exists():
            return True

        # Business area leader can generate
        if obj.project.business_area.leader == request.user:
            return True

        return False
