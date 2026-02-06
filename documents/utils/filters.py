"""
Document filtering utilities
"""
from django.db.models import Q


def apply_document_filters(queryset, filters):
    """
    Apply filters to document queryset
    
    Args:
        queryset: Base document queryset
        filters: Dict of filter parameters
        
    Returns:
        Filtered queryset
    """
    # Search term
    search_term = filters.get('searchTerm') or filters.get('search')
    if search_term:
        queryset = queryset.filter(
            Q(project__title__icontains=search_term) |
            Q(project__description__icontains=search_term) |
            Q(kind__icontains=search_term)
        )
    
    # Kind filter
    kind = filters.get('kind')
    if kind and kind != 'All':
        queryset = queryset.filter(kind=kind)
    
    # Status filter
    status = filters.get('status')
    if status and status != 'All':
        queryset = queryset.filter(status=status)
    
    # Project filter
    project_id = filters.get('project') or filters.get('project_id')
    if project_id:
        queryset = queryset.filter(project__pk=project_id)
    
    # Year filter
    year = filters.get('year')
    if year and year != 'All':
        queryset = queryset.filter(project__year=year)
    
    # Business area filter
    business_area = filters.get('business_area')
    if business_area and business_area != 'All':
        queryset = queryset.filter(project__business_area__pk=business_area)
    
    # Approval status filters
    approved_only = filters.get('approved_only')
    if approved_only:
        queryset = queryset.filter(status='approved')
    
    pending_approval = filters.get('pending_approval')
    if pending_approval:
        queryset = queryset.filter(status='inapproval')
    
    return queryset


def apply_annual_report_filters(queryset, filters):
    """
    Apply filters to annual report queryset
    
    Args:
        queryset: Base annual report queryset
        filters: Dict of filter parameters
        
    Returns:
        Filtered queryset
    """
    # Year filter
    year = filters.get('year')
    if year and year != 'All':
        queryset = queryset.filter(year=year)
    
    # Published filter
    published_only = filters.get('published_only')
    if published_only:
        queryset = queryset.filter(is_published=True)
    
    # Date range filters
    date_from = filters.get('date_from')
    if date_from:
        queryset = queryset.filter(date_open__gte=date_from)
    
    date_to = filters.get('date_to')
    if date_to:
        queryset = queryset.filter(date_closed__lte=date_to)
    
    return queryset
