"""
User permission classes
"""

from rest_framework.permissions import BasePermission


class CanManageUser(BasePermission):
    """
    Permission to manage users

    Users can manage themselves, admins can manage any user
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj == request.user


class CanManageProfile(BasePermission):
    """
    Permission to manage user profiles

    Users can manage their own profile, admins can manage any profile
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user


class CanViewProfile(BasePermission):
    """
    Permission to view profiles

    Public profiles visible to all, private profiles visible to owner and admins
    """

    def has_object_permission(self, request, view, obj):
        # Public profiles visible to all
        if hasattr(obj, "public") and obj.public:
            return True

        # Owner can view their own profile
        if obj.user == request.user:
            return True

        # Admins can view any profile
        if request.user.is_superuser:
            return True

        return False


class CanManageStaffProfile(BasePermission):
    """
    Permission to manage staff profiles

    Users can manage their own staff profile, admins can manage any
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user


class CanExportData(BasePermission):
    """
    Permission to export data

    Only admins can export data
    """

    def has_permission(self, request, view):
        return request.user.is_superuser


class CanManageEmploymentEntry(BasePermission):
    """
    Permission to manage employment entries

    Users can manage their own entries, admins can manage any
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.public_profile.user == request.user


class CanManageEducationEntry(BasePermission):
    """
    Permission to manage education entries

    Users can manage their own entries, admins can manage any
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.public_profile.user == request.user
