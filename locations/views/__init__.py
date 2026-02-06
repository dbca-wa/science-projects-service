"""
Location views
"""
from .crud import Areas, AreaDetail
from .area_types import DBCADistricts, DBCARegions, Imcras, Ibras, Nrms

__all__ = [
    'Areas',
    'AreaDetail',
    'DBCADistricts',
    'DBCARegions',
    'Imcras',
    'Ibras',
    'Nrms',
]
