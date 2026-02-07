"""
Common serializer classes and mixins for DRY backend architecture
"""

from .base import BaseModelSerializer, TimestampedSerializer

__all__ = [
    "BaseModelSerializer",
    "TimestampedSerializer",
]
