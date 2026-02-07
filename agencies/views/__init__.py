# Export all views for backward compatibility
from .affiliations import (
    AffiliationDetail,
    Affiliations,
    AffiliationsCleanOrphaned,
    AffiliationsMerge,
)
from .agencies import Agencies, AgencyDetail
from .branches import BranchDetail, Branches
from .business_areas import (
    BusinessAreaDetail,
    BusinessAreas,
    BusinessAreasProblematicProjects,
    BusinessAreasUnapprovedDocs,
    MyBusinessAreas,
    SetBusinessAreaActive,
)
from .divisions import DivisionDetail, DivisionEmailList, Divisions
from .services import DepartmentalServiceDetail, DepartmentalServices

__all__ = [
    # Affiliations
    "Affiliations",
    "AffiliationDetail",
    "AffiliationsMerge",
    "AffiliationsCleanOrphaned",
    # Agencies
    "Agencies",
    "AgencyDetail",
    # Branches
    "Branches",
    "BranchDetail",
    # Business Areas
    "BusinessAreas",
    "BusinessAreaDetail",
    "MyBusinessAreas",
    "BusinessAreasUnapprovedDocs",
    "BusinessAreasProblematicProjects",
    "SetBusinessAreaActive",
    # Divisions
    "Divisions",
    "DivisionDetail",
    "DivisionEmailList",
    # Departmental Services
    "DepartmentalServices",
    "DepartmentalServiceDetail",
]
