"""
Common backend utilities and base classes

This module provides shared utilities for DRY backend architecture:
- Base view classes and mixins
- Base serializer classes
- Common permission classes
- Utility functions for pagination, filtering, validation

Usage:
    from common.views import BaseAPIView, SerializerValidationMixin
    from common.serializers import BaseModelSerializer
    from common.permissions import IsAdminUser
    from common.utils import paginate_queryset, apply_search_filter
"""

__version__ = '1.0.0'
