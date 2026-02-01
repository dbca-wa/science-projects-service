# Export all views for backward compatibility
from .affiliations import (
    Affiliations,
    AffiliationDetail,
    AffiliationsMerge,
    AffiliationsCleanOrphaned,
)
from .agencies import Agencies, AgencyDetail
from .branches import Branches, BranchDetail
from .business_areas import (
    BusinessAreas,
    BusinessAreaDetail,
    MyBusinessAreas,
    BusinessAreasUnapprovedDocs,
    BusinessAreasProblematicProjects,
    SetBusinessAreaActive,
)
from .divisions import Divisions, DivisionDetail, DivisionEmailList
from .services import DepartmentalServices, DepartmentalServiceDetail

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
