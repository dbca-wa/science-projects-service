"""
Project filtering utilities
"""
from django.db.models import Q, CharField
from django.db.models.functions import Cast

from ..models import Project


def determine_db_kind(provided):
    """
    Determine database kind from project tag prefix
    
    Args:
        provided: Project tag prefix (e.g., "CF", "SP")
        
    Returns:
        Database kind string or None
    """
    if provided.startswith("CF"):
        return "core_function"
    elif provided.startswith("STP"):
        return "student"
    elif provided.startswith("SP"):
        return "science"
    elif provided.startswith("EXT"):
        return "external"
    return None


def parse_project_tag_search(search_term):
    """
    Parse project tag search term (e.g., CF-2022-123)
    
    Args:
        search_term: Search string
        
    Returns:
        QuerySet of Project objects
    """
    if not search_term:
        return Project.objects.none()
    
    parts = search_term.split("-")
    
    if not parts or not parts[0]:
        return Project.objects.none()
    
    db_kind = determine_db_kind(parts[0].upper())
    if not db_kind:
        return Project.objects.none()
    
    projects = Project.objects.filter(kind=db_kind)
    
    # Case: prefix-year-number (e.g., "CF-2022-123")
    if len(parts) >= 3:
        if parts[1] and parts[1].strip():
            try:
                year_as_int = int(parts[1])
                if len(parts[1]) == 4:
                    projects = projects.filter(year=year_as_int)
            except (ValueError, TypeError):
                pass
        
        if parts[2] and parts[2].strip():
            try:
                number_as_int = int(parts[2])
                projects = projects.filter(number__icontains=number_as_int)
            except (ValueError, TypeError):
                pass
    
    # Case: prefix-year (e.g., "CF-2022")
    elif len(parts) == 2:
        if parts[1] and parts[1].strip():
            try:
                year_as_int = int(parts[1])
                if len(parts[1]) == 4:
                    projects = projects.filter(year=year_as_int)
            except (ValueError, TypeError):
                pass
    
    return projects


def is_project_tag_search(search_term):
    """
    Check if search term is a project tag (e.g., CF-2022-123)
    
    Args:
        search_term: Search string
        
    Returns:
        Boolean
    """
    if not search_term:
        return False
    lower_term = search_term.lower()
    return (
        lower_term.startswith("cf-")
        or lower_term.startswith("sp-")
        or lower_term.startswith("stp-")
        or lower_term.startswith("ext-")
    )


def apply_project_filters(queryset, filters):
    """
    Apply filters to project queryset
    
    Args:
        queryset: Base Project queryset
        filters: Dict of filter parameters
        
    Returns:
        Filtered queryset
    """
    # Search term
    search_term = filters.get("searchTerm")
    if search_term:
        if is_project_tag_search(search_term):
            queryset = parse_project_tag_search(search_term)
        else:
            queryset = queryset.annotate(
                number_as_text=Cast("number", output_field=CharField())
            ).filter(
                Q(title__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(tagline__icontains=search_term)
                | Q(keywords__icontains=search_term)
                | Q(number_as_text__icontains=search_term)
            )
    
    # User filter
    selected_user = filters.get("selected_user")
    if selected_user:
        queryset = queryset.filter(members__user__pk=selected_user)
    
    # Business area filter
    business_area = filters.get("businessarea")
    if business_area and business_area != "All":
        if isinstance(business_area, str) and "," in business_area:
            business_areas = business_area.split(",")
            queryset = queryset.filter(business_area__pk__in=business_areas)
        else:
            queryset = queryset.filter(business_area__pk=business_area)
    
    # Status filter
    status_slug = filters.get("projectstatus", "All")
    if status_slug != "All":
        if status_slug == "unknown":
            queryset = queryset.exclude(status__in=Project.StatusChoices.values)
        else:
            queryset = queryset.filter(status=status_slug)
    
    # Kind filter
    kind_slug = filters.get("projectkind", "All")
    if kind_slug != "All":
        queryset = queryset.filter(kind=kind_slug)
    
    # Year filter
    year_filter = filters.get("year", "All")
    if year_filter != "All":
        queryset = queryset.filter(year=year_filter)
    
    # Active/inactive filters
    only_active = filters.get("only_active", False)
    only_inactive = filters.get("only_inactive", False)
    
    if only_active:
        queryset = queryset.filter(status__in=Project.ACTIVE_ONLY)
    elif only_inactive:
        queryset = queryset.exclude(status__in=Project.ACTIVE_ONLY)
    
    return queryset
