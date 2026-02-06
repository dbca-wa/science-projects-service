"""
Documents views
"""
# CRUD views
from .crud import (
    ProjectDocuments,
    ProjectDocumentDetail,
    ProjectDocsPendingMyAction,
)

# Approval views
from .approval import (
    DocApproval,
    DocRecall,
    DocSendBack,
    RequestApproval,
    ApproveStageOne,
    ApproveStageTwo,
    ApproveStageThree,
    SendBack,
    RecallDocument,
    BatchApprove,
)

# PDF views
from .pdf import (
    DownloadProjectDocument,
    BeginProjectDocGeneration,
    CancelProjectDocGeneration,
    DownloadAnnualReport,
    BeginAnnualReportDocGeneration,
    CancelReportDocGeneration,
)

# Concept plan views
from .concept_plan import (
    ConceptPlans,
    ConceptPlanDetail,
    GetConceptPlanData,
)

# Project plan views
from .project_plan import (
    ProjectPlans,
    ProjectPlanDetail,
)

# Progress report views
from .progress_report import (
    ProgressReports,
    ProgressReportDetail,
    UpdateProgressReport,
    ProgressReportByYear,
)

# Student report views
from .student_report import (
    StudentReports,
    StudentReportDetail,
    StudentReportByYear,
    UpdateStudentReport,
)

# Closure views
from .closure import (
    ProjectClosures,
    ProjectClosureDetail,
)

# Endorsement views
from .endorsement import (
    Endorsements,
    EndorsementDetail,
    EndorsementsPendingMyAction,
    SeekEndorsement,
    DeleteAECEndorsement,
)

# Custom publication views
from .custom_publication import (
    CustomPublications,
    CustomPublicationDetail,
)

# Admin views
from .admin import (
    ProjectDocsPendingMyActionAllStages,
    # ProjectDocumentComments,  # TODO: Comment model not yet implemented
    DocumentSpawner,
    GetPreviousReportsData,
    ReopenProject,
    BatchApproveOld,
    FinalDocApproval,
)

# Annual report views
from .annual_report import (
    Reports,
    ReportDetail,
    GetLatestReportYear,
    GetAvailableReportYearsForStudentReport,
    GetAvailableReportYearsForProgressReport,
    GetWithoutPDFs,
    GetReportPDF,
    GetWithPDFs,
    GetLegacyPDFs,
    GetCompletedReports,
    # BeginAnnualReportDocGeneration,  # Removed duplicate - use the one from pdf.py
    LatestYearsProgressReports,
    LatestYearsStudentReports,
    LatestYearsInactiveReports,
    FullLatestReport,
)

# Notification views
from .notifications import (
    NewCycleOpen,
    SendBumpEmails,
    UserPublications,
    SendMentionNotification,
)

__all__ = [
    # CRUD
    'ProjectDocuments',
    'ProjectDocumentDetail',
    'ProjectDocsPendingMyAction',
    # Approval
    'DocApproval',
    'DocRecall',
    'DocSendBack',
    'RequestApproval',
    'ApproveStageOne',
    'ApproveStageTwo',
    'ApproveStageThree',
    'SendBack',
    'RecallDocument',
    'BatchApprove',
    # PDF
    'DownloadProjectDocument',
    'BeginProjectDocGeneration',
    'CancelProjectDocGeneration',
    'DownloadAnnualReport',
    'BeginAnnualReportDocGeneration',
    'CancelReportDocGeneration',
    # Concept plan
    'ConceptPlans',
    'ConceptPlanDetail',
    'GetConceptPlanData',
    # Project plan
    'ProjectPlans',
    'ProjectPlanDetail',
    # Progress report
    'ProgressReports',
    'ProgressReportDetail',
    'UpdateProgressReport',
    'ProgressReportByYear',
    # Student report
    'StudentReports',
    'StudentReportDetail',
    'StudentReportByYear',
    'UpdateStudentReport',
    # Closure
    'ProjectClosures',
    'ProjectClosureDetail',
    # Endorsement
    'Endorsements',
    'EndorsementDetail',
    'EndorsementsPendingMyAction',
    'SeekEndorsement',
    'DeleteAECEndorsement',
    # Custom publication
    'CustomPublications',
    'CustomPublicationDetail',
    # Admin
    'ProjectDocsPendingMyActionAllStages',
    # 'ProjectDocumentComments',  # TODO: Comment model not yet implemented
    'DocumentSpawner',
    'GetPreviousReportsData',
    'ReopenProject',
    'BatchApproveOld',
    'FinalDocApproval',
    # Annual report
    'Reports',
    'ReportDetail',
    'GetLatestReportYear',
    'GetAvailableReportYearsForStudentReport',
    'GetAvailableReportYearsForProgressReport',
    'GetWithoutPDFs',
    'GetReportPDF',
    'GetWithPDFs',
    'GetLegacyPDFs',
    'GetCompletedReports',
    'BeginAnnualReportDocGeneration',
    'LatestYearsProgressReports',
    'LatestYearsStudentReports',
    'LatestYearsInactiveReports',
    'FullLatestReport',
    # Notification
    'NewCycleOpen',
    'SendBumpEmails',
    'UserPublications',
    'SendMentionNotification',
]
