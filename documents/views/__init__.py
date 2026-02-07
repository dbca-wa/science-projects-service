"""
Documents views
"""

# Admin views
from .admin import (  # ProjectDocumentComments,  # TODO: Comment model not yet implemented
    BatchApproveOld,
    DocumentSpawner,
    FinalDocApproval,
    GetPreviousReportsData,
    ProjectDocsPendingMyActionAllStages,
    ReopenProject,
)

# Annual report views
from .annual_report import (  # BeginAnnualReportDocGeneration,  # Removed duplicate - use the one from pdf.py
    FullLatestReport,
    GetAvailableReportYearsForProgressReport,
    GetAvailableReportYearsForStudentReport,
    GetCompletedReports,
    GetLatestReportYear,
    GetLegacyPDFs,
    GetReportPDF,
    GetWithoutPDFs,
    GetWithPDFs,
    LatestYearsInactiveReports,
    LatestYearsProgressReports,
    LatestYearsStudentReports,
    ReportDetail,
    Reports,
)

# Approval views
from .approval import (
    ApproveStageOne,
    ApproveStageThree,
    ApproveStageTwo,
    BatchApprove,
    DocApproval,
    DocRecall,
    DocSendBack,
    RecallDocument,
    RequestApproval,
    SendBack,
)

# Closure views
from .closure import ProjectClosureDetail, ProjectClosures

# Concept plan views
from .concept_plan import ConceptPlanDetail, ConceptPlans, GetConceptPlanData

# CRUD views
from .crud import ProjectDocsPendingMyAction, ProjectDocumentDetail, ProjectDocuments

# Custom publication views
from .custom_publication import CustomPublicationDetail, CustomPublications

# Endorsement views
from .endorsement import (
    DeleteAECEndorsement,
    EndorsementDetail,
    Endorsements,
    EndorsementsPendingMyAction,
    SeekEndorsement,
)

# Notification views
from .notifications import (
    NewCycleOpen,
    SendBumpEmails,
    SendMentionNotification,
    UserPublications,
)

# PDF views
from .pdf import (
    BeginAnnualReportDocGeneration,
    BeginProjectDocGeneration,
    CancelProjectDocGeneration,
    CancelReportDocGeneration,
    DownloadAnnualReport,
    DownloadProjectDocument,
)

# Progress report views
from .progress_report import (
    ProgressReportByYear,
    ProgressReportDetail,
    ProgressReports,
    UpdateProgressReport,
)

# Project plan views
from .project_plan import ProjectPlanDetail, ProjectPlans

# Student report views
from .student_report import (
    StudentReportByYear,
    StudentReportDetail,
    StudentReports,
    UpdateStudentReport,
)

__all__ = [
    # CRUD
    "ProjectDocuments",
    "ProjectDocumentDetail",
    "ProjectDocsPendingMyAction",
    # Approval
    "DocApproval",
    "DocRecall",
    "DocSendBack",
    "RequestApproval",
    "ApproveStageOne",
    "ApproveStageTwo",
    "ApproveStageThree",
    "SendBack",
    "RecallDocument",
    "BatchApprove",
    # PDF
    "DownloadProjectDocument",
    "BeginProjectDocGeneration",
    "CancelProjectDocGeneration",
    "DownloadAnnualReport",
    "BeginAnnualReportDocGeneration",
    "CancelReportDocGeneration",
    # Concept plan
    "ConceptPlans",
    "ConceptPlanDetail",
    "GetConceptPlanData",
    # Project plan
    "ProjectPlans",
    "ProjectPlanDetail",
    # Progress report
    "ProgressReports",
    "ProgressReportDetail",
    "UpdateProgressReport",
    "ProgressReportByYear",
    # Student report
    "StudentReports",
    "StudentReportDetail",
    "StudentReportByYear",
    "UpdateStudentReport",
    # Closure
    "ProjectClosures",
    "ProjectClosureDetail",
    # Endorsement
    "Endorsements",
    "EndorsementDetail",
    "EndorsementsPendingMyAction",
    "SeekEndorsement",
    "DeleteAECEndorsement",
    # Custom publication
    "CustomPublications",
    "CustomPublicationDetail",
    # Admin
    "ProjectDocsPendingMyActionAllStages",
    # 'ProjectDocumentComments',  # TODO: Comment model not yet implemented
    "DocumentSpawner",
    "GetPreviousReportsData",
    "ReopenProject",
    "BatchApproveOld",
    "FinalDocApproval",
    # Annual report
    "Reports",
    "ReportDetail",
    "GetLatestReportYear",
    "GetAvailableReportYearsForStudentReport",
    "GetAvailableReportYearsForProgressReport",
    "GetWithoutPDFs",
    "GetReportPDF",
    "GetWithPDFs",
    "GetLegacyPDFs",
    "GetCompletedReports",
    "BeginAnnualReportDocGeneration",
    "LatestYearsProgressReports",
    "LatestYearsStudentReports",
    "LatestYearsInactiveReports",
    "FullLatestReport",
    # Notification
    "NewCycleOpen",
    "SendBumpEmails",
    "UserPublications",
    "SendMentionNotification",
]
