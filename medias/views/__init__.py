"""
Views for media management
"""

from .project_docs import ProjectDocPDFS
from .annual_reports import (
    AnnualReportPDFs,
    AnnualReportPDFDetail,
    LegacyAnnualReportPDFs,
    LegacyAnnualReportPDFDetail,
    AnnualReportMedias,
    AnnualReportMediaDetail,
    LatestReportMedia,
    AnnualReportMediaUpload,
    AnnualReportMediaDelete,
)
from .photos import (
    BusinessAreaPhotos,
    BusinessAreaPhotoDetail,
    ProjectPhotos,
    ProjectPhotoDetail,
    MethodologyPhotos,
    MethodologyPhotoDetail,
    AgencyPhotos,
    AgencyPhotoDetail,
)
from .avatars import UserAvatars, UserAvatarDetail

__all__ = [
    # Project documents
    "ProjectDocPDFS",
    # Annual reports
    "AnnualReportPDFs",
    "AnnualReportPDFDetail",
    "LegacyAnnualReportPDFs",
    "LegacyAnnualReportPDFDetail",
    "AnnualReportMedias",
    "AnnualReportMediaDetail",
    "LatestReportMedia",
    "AnnualReportMediaUpload",
    "AnnualReportMediaDelete",
    # Photos
    "BusinessAreaPhotos",
    "BusinessAreaPhotoDetail",
    "ProjectPhotos",
    "ProjectPhotoDetail",
    "MethodologyPhotos",
    "MethodologyPhotoDetail",
    "AgencyPhotos",
    "AgencyPhotoDetail",
    # Avatars
    "UserAvatars",
    "UserAvatarDetail",
]
