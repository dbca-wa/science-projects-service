"""
Pagination utilities for consistent list view pagination
"""

from math import ceil

from django.conf import settings


def paginate_queryset(queryset, request):
    """
    Paginate queryset based on request parameters

    Args:
        queryset: QuerySet to paginate
        request: HTTP request with query parameters

    Returns:
        Dict with pagination data:
        {
            'items': paginated_queryset,
            'total_results': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
        }

    Example:
        from common.utils.pagination import paginate_queryset

        paginated = paginate_queryset(projects, request)
        serializer = ProjectSerializer(paginated['items'], many=True)
        return Response({
            'results': serializer.data,
            'total_results': paginated['total_results'],
            'total_pages': paginated['total_pages'],
        })
    """
    try:
        page = int(request.query_params.get("page", 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    page_size = getattr(settings, "PAGE_SIZE", 20)

    # Handle custom page_size from request
    try:
        custom_page_size = int(request.query_params.get("page_size", page_size))
        if 1 <= custom_page_size <= 100:  # Limit max page size
            page_size = custom_page_size
    except (ValueError, TypeError):
        pass

    start = (page - 1) * page_size
    end = start + page_size

    total_count = queryset.count()
    total_pages = ceil(total_count / page_size) if page_size > 0 else 0

    return {
        "items": queryset[start:end],
        "total_results": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
    }


def get_page_number(request, default=1):
    """
    Extract page number from request

    Args:
        request: HTTP request
        default: Default page number if not provided or invalid

    Returns:
        Integer page number
    """
    try:
        page = int(request.query_params.get("page", default))
        return max(1, page)  # Ensure page is at least 1
    except (ValueError, TypeError):
        return default


def get_page_size(request, default=None):
    """
    Extract page size from request

    Args:
        request: HTTP request
        default: Default page size (uses settings.PAGE_SIZE if None)

    Returns:
        Integer page size
    """
    if default is None:
        default = getattr(settings, "PAGE_SIZE", 20)

    try:
        page_size = int(request.query_params.get("page_size", default))
        # Limit between 1 and 100
        return max(1, min(100, page_size))
    except (ValueError, TypeError):
        return default
