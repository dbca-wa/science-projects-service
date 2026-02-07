"""
Common view classes and mixins for DRY backend architecture
"""

from .base import BaseAPIView
from .mixins import PaginationMixin, SerializerValidationMixin

__all__ = [
    "BaseAPIView",
    "SerializerValidationMixin",
    "PaginationMixin",
]
