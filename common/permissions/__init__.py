"""
Common permission classes for DRY backend architecture
"""
from .base import IsAdminUser, IsOwnerOrAdmin

__all__ = [
    'IsAdminUser',
    'IsOwnerOrAdmin',
]
