"""
Common utilities for DRY backend architecture
"""

from .filters import (
    apply_boolean_filter,
    apply_date_range_filter,
    apply_search_filter,
    apply_status_filter,
)
from .mixins import ProjectTeamMemberMixin, TeamMemberMixin
from .pagination import get_page_number, get_page_size, paginate_queryset
from .validators import (
    validate_date_range,
    validate_file_extension,
    validate_file_size,
    validate_not_empty,
    validate_positive_number,
)

__all__ = [
    # Pagination
    "paginate_queryset",
    "get_page_number",
    "get_page_size",
    # Filters
    "apply_search_filter",
    "apply_date_range_filter",
    "apply_status_filter",
    "apply_boolean_filter",
    # Validators
    "validate_not_empty",
    "validate_date_range",
    "validate_positive_number",
    "validate_file_size",
    "validate_file_extension",
    # Mixins
    "TeamMemberMixin",
    "ProjectTeamMemberMixin",
]
