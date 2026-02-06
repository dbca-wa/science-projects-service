"""
Common view classes and mixins for DRY backend architecture
"""
from .base import BaseAPIView
from .mixins import SerializerValidationMixin, PaginationMixin

__all__ = [
    'BaseAPIView',
    'SerializerValidationMixin',
    'PaginationMixin',
]
