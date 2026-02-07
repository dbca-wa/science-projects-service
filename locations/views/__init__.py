"""
Location views
"""

from .area_types import DBCADistricts, DBCARegions, Ibras, Imcras, Nrms
from .crud import AreaDetail, Areas

__all__ = [
    "Areas",
    "AreaDetail",
    "DBCADistricts",
    "DBCARegions",
    "Imcras",
    "Ibras",
    "Nrms",
]
