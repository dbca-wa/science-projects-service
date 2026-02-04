"""
Documents permissions
"""
from .document_permissions import (
    CanViewDocument,
    CanEditDocument,
    CanApproveDocument,
    CanRecallDocument,
    CanDeleteDocument,
    CanGeneratePDF,
)
from .annual_report_permissions import (
    CanViewAnnualReport,
    CanEditAnnualReport,
    CanPublishAnnualReport,
    CanGenerateAnnualReportPDF,
)

__all__ = [
    'CanViewDocument',
    'CanEditDocument',
    'CanApproveDocument',
    'CanRecallDocument',
    'CanDeleteDocument',
    'CanGeneratePDF',
    'CanViewAnnualReport',
    'CanEditAnnualReport',
    'CanPublishAnnualReport',
    'CanGenerateAnnualReportPDF',
]
