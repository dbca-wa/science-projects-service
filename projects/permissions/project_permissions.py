"""
Project permission classes
"""

from rest_framework.permissions import BasePermission


class CanViewProject(BasePermission):
    """
    Permission to view a project
    All authenticated users can view projects
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated


class CanEditProject(BasePermission):
    """
    Permission to edit a project
    Only project leaders and superusers can edit
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Check if user is project leader
        return obj.members.filter(user=request.user, is_leader=True).exists()


class CanManageProjectMembers(BasePermission):
    """
    Permission to manage project members
    Only project leaders and superusers can manage members
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Check if user is project leader
        return obj.members.filter(user=request.user, is_leader=True).exists()


class IsProjectLeader(BasePermission):
    """
    Permission check for project leaders
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Check if user is project leader
        return obj.members.filter(user=request.user, is_leader=True).exists()


class IsProjectMember(BasePermission):
    """
    Permission check for project members
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Check if user is a member of the project
        return obj.members.filter(user=request.user).exists()
