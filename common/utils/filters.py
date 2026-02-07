"""
Common filtering utilities for QuerySet filtering
"""

from django.db.models import Q


def apply_search_filter(queryset, search_term, fields):
    """
    Apply search filter across multiple fields

    Args:
        queryset: Base QuerySet
        search_term: Search string
        fields: List of field names to search

    Returns:
        Filtered QuerySet

    Example:
        queryset = apply_search_filter(
            Project.objects.all(),
            "test",
            ['title', 'description']
        )
    """
    if not search_term or not fields:
        return queryset

    q_objects = Q()
    for field in fields:
        q_objects |= Q(**{f"{field}__icontains": search_term})

    return queryset.filter(q_objects)


def apply_date_range_filter(queryset, field_name, start_date=None, end_date=None):
    """
    Apply date range filter to queryset

    Args:
        queryset: Base QuerySet
        field_name: Name of date field to filter
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        Filtered QuerySet

    Example:
        queryset = apply_date_range_filter(
            Project.objects.all(),
            'created_at',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
    """
    if start_date:
        queryset = queryset.filter(**{f"{field_name}__gte": start_date})

    if end_date:
        queryset = queryset.filter(**{f"{field_name}__lte": end_date})

    return queryset


def apply_status_filter(queryset, status_param, field_name="status"):
    """
    Apply status filter to queryset

    Args:
        queryset: Base QuerySet
        status_param: Status value or list of statuses
        field_name: Name of status field (default: 'status')

    Returns:
        Filtered QuerySet

    Example:
        queryset = apply_status_filter(
            Project.objects.all(),
            ['active', 'pending']
        )
    """
    if not status_param:
        return queryset

    if isinstance(status_param, (list, tuple)):
        return queryset.filter(**{f"{field_name}__in": status_param})

    return queryset.filter(**{field_name: status_param})


def apply_boolean_filter(queryset, param_value, field_name):
    """
    Apply boolean filter to queryset

    Args:
        queryset: Base QuerySet
        param_value: Boolean value or string ('true', 'false', '1', '0')
        field_name: Name of boolean field

    Returns:
        Filtered QuerySet

    Example:
        queryset = apply_boolean_filter(
            Project.objects.all(),
            'true',
            'is_active'
        )
    """
    if param_value is None:
        return queryset

    # Convert string to boolean
    if isinstance(param_value, str):
        param_value = param_value.lower() in ("true", "1", "yes")

    return queryset.filter(**{field_name: param_value})
