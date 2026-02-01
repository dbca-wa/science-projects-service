"""
Location views - Compatibility layer
"""
from .views.crud import Areas, AreaDetail
from .views.area_types import DBCADistricts, DBCARegions, Imcras, Ibras, Nrms

__all__ = [
    'Areas',
    'AreaDetail',
    'DBCADistricts',
    'DBCARegions',
    'Imcras',
    'Ibras',
    'Nrms',
]
