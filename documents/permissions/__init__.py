"""
Documents permissions
"""

from .annual_report_permissions import (
    CanEditAnnualReport,
    CanGenerateAnnualReportPDF,
    CanPublishAnnualReport,
    CanViewAnnualReport,
)
from .document_permissions import (
    CanApproveDocument,
    CanDeleteDocument,
    CanEditDocument,
    CanGeneratePDF,
    CanRecallDocument,
    CanViewDocument,
)

__all__ = [
    "CanViewDocument",
    "CanEditDocument",
    "CanApproveDocument",
    "CanRecallDocument",
    "CanDeleteDocument",
    "CanGeneratePDF",
    "CanViewAnnualReport",
    "CanEditAnnualReport",
    "CanPublishAnnualReport",
    "CanGenerateAnnualReportPDF",
]
