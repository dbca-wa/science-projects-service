"""
User filtering utilities
"""


def apply_user_filters(queryset, filters):
    """
    Apply filters to user queryset

    Args:
        queryset: Base User queryset
        filters: Dict of filter parameters

    Returns:
        Filtered queryset
    """
    if "is_active" in filters:
        queryset = queryset.filter(is_active=filters["is_active"])

    if "is_staff" in filters:
        queryset = queryset.filter(is_staff=filters["is_staff"])

    if "is_superuser" in filters:
        queryset = queryset.filter(is_superuser=filters["is_superuser"])

    if "business_area" in filters:
        queryset = queryset.filter(work__business_area_id=filters["business_area"])

    if "directorate" in filters:
        queryset = queryset.filter(
            work__business_area__division__directorate_id=filters["directorate"]
        )

    return queryset


def apply_profile_filters(queryset, filters):
    """
    Apply filters to profile queryset

    Args:
        queryset: Base PublicStaffProfile queryset
        filters: Dict of filter parameters

    Returns:
        Filtered queryset
    """
    if "is_active" in filters:
        queryset = queryset.filter(is_active=filters["is_active"])

    if "public" in filters:
        queryset = queryset.filter(public=filters["public"])

    if "business_area" in filters:
        queryset = queryset.filter(
            user__work__business_area_id=filters["business_area"]
        )

    if "user" in filters:
        queryset = queryset.filter(user_id=filters["user"])

    return queryset
