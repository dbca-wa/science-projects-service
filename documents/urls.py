from django.urls import path
from . import views

urlpatterns = [
    # Reports ========================================================
    path("reports", views.Reports.as_view()),
    path("reports/<int:pk>", views.ReportDetail.as_view()),
    path("reports/download", views.DownloadAnnualReport.as_view()),
    path("reports/latestyear", views.GetLatestReportYear.as_view()),
    path(
        "reports/availableyears/<int:project_pk>/progressreport",
        views.GetAvailableReportYearsForProgressReport.as_view(),
    ),
    path(
        "reports/availableyears/<int:project_pk>/studentreport",
        views.GetAvailableReportYearsForStudentReport.as_view(),
    ),
    path("reports/withoutPDF", views.GetWithoutPDFs.as_view()),
    path("reports/withPDF", views.GetWithPDFs.as_view()),
    path("reports/legacyPDF", views.GetLegacyPDFs.as_view()),
    path("reports/pdf/<int:pk>", views.GetReportPDF.as_view()),
    path("reports/completed", views.GetCompletedReports.as_view()),
    # PR Population
    path("get_previous_reports_data", views.GetPreviousReportsData.as_view()),
    # Latest Report's active PRs and SRs ========================================================
    path("latest_active_progress_reports", views.LatestYearsProgressReports.as_view()),
    path("latest_active_student_reports", views.LatestYearsStudentReports.as_view()),
    path("latest_inactive_reports", views.LatestYearsInactiveReports.as_view()),
    path("reports/latest", views.FullLatestReport.as_view()),
    # Annual Report Gen ========================================================
    path("reports/<int:pk>/generate_pdf", views.BeginReportDocGeneration.as_view()),
    path(
        "reports/<int:pk>/unapproved_generate_pdf",
        views.BeginUnapprovedReportDocGeneration.as_view(),
    ),
    path(
        "reports/<int:pk>/cancel_doc_gen",
        views.CancelReportDocGeneration.as_view(),
    ),
    # Admin Latest Report ========================================================
    path("actions/finalApproval", views.FinalDocApproval.as_view()),
    path("student_reports/update_progress", views.UpdateStudentReport.as_view()),
    path("progress_reports/update", views.UpdateProgressReport.as_view()),
    # Endorsements ========================================================
    path("endorsements", views.ProjectDocuments.as_view()),
    path("endorsements/pendingmyaction", views.EndorsementsPendingMyAction.as_view()),
    # Project Documents ========================================================
    path("spawn", views.DocumentSpawner.as_view()),
    path("projectdocuments", views.ProjectDocuments.as_view()),
    path("projectdocuments/<int:pk>", views.ProjectDocumentDetail.as_view()),
    path("conceptplans", views.ConceptPlans.as_view()),
    path("conceptplans/<int:pk>", views.ConceptPlanDetail.as_view()),
    path("projectplans", views.ProjectPlans.as_view()),
    path("projectplans/<int:pk>", views.ProjectPlanDetail.as_view()),
    path("progressreports", views.ProgressReports.as_view()),
    path("progressreports/<int:pk>", views.ProgressReportDetail.as_view()),
    path("studentreports", views.StudentReports.as_view()),
    path("studentreports/<int:pk>", views.StudentReportDetail.as_view()),
    path("projectclosures", views.ProjectClosures.as_view()),
    path("projectclosures/<int:pk>", views.ProjectClosureDetail.as_view()),
    # Project Documents Secondary ========================================================
    path("projectdocuments/<int:pk>/comments", views.ProjectDocumentComments.as_view()),
    path(
        "projectdocuments/pendingmyaction",
        views.ProjectDocsPendingMyActionAllStages.as_view(),
    ),
    path(
        "projectdocuments/pendingmyaction/stage1",
        views.ProjectDocsPendingMyActionStageOne.as_view(),
    ),
    path(
        "projectdocuments/pendingmyaction/stage2",
        views.ProjectDocsPendingMyActionStageTwo.as_view(),
    ),
    path(
        "projectdocuments/pendingmyaction/stage3",
        views.ProjectDocsPendingMyActionStageThree.as_view(),
    ),
    path("projectplans/endorsements", views.Endorsements.as_view()),
    path(
        "projectplans/endorsements/<int:pk>",
        views.EndorsementDetail.as_view(),
    ),
    path(
        "project_plans/<int:pk>/seek_endorsement",
        views.SeekEndorsement.as_view(),
    ),
    path(
        "project_plans/<int:pk>/delete_aec_endorsement_pdf",
        views.DeleteAECEndorsement.as_view(),
    ),
    path(
        "progressreports/<int:project>/<int:year>",
        views.ProgressReportByYear.as_view(),
    ),
    path(
        "studentreports/<int:project>/<int:year>",
        views.StudentReportByYear.as_view(),
    ),
    path(
        "conceptplans/<int:pk>/get_concept_plan_data",
        views.GetConceptPlanData.as_view(),
    ),
    # Project Doc Gen ========================================================
    path(
        "generate_project_document/<int:pk>", views.BeginProjectDocGeneration.as_view()
    ),
    path("cancel_doc_gen/<int:pk>", views.CancelProjectDocGeneration.as_view()),
    # EMAILS (Testing) ========================================================
    path("concept_plan_email", views.ConceptPlanEmail.as_view()),
    path("review_document_email", views.ReviewDocumentEmail.as_view()),
    path("new_cycle_email", views.NewCycleOpenEmail.as_view()),
    path("project_closure_email", views.ProjectClosureEmail.as_view()),
    path("document_ready_email", views.DocumentReadyEmail.as_view()),
    path("document_sent_back_email", views.DocumentSentBackEmail.as_view()),
    path("document_approved_email", views.DocumentApprovedEmail.as_view()),
    path("document_recalled_email", views.DocumentRecalledEmail.as_view()),
    path("spms_link_email", views.SPMSInviteEmail.as_view()),
    path("get_project_lead_emails", views.GetProjectLeadEmail.as_view()),
    # ACTIONS (Sends emails) ========================================================
    path("opennewcycle", views.NewCycleOpen.as_view()),
    path("batchapprove", views.BatchApprove.as_view()),
    path("batchapproveold", views.BatchApproveOld.as_view()),
    path("projectclosures/reopen/<int:pk>", views.RepoenProject.as_view()),
    # Actions (Project Docs - Sends emails) ========================================================
    path("actions/approve", views.DocApproval.as_view(), name="document-approve"),
    path("actions/recall", views.DocRecall.as_view(), name="document-recall"),
    path("actions/send_back", views.DocSendBack.as_view(), name="document-send-back"),
    path("actions/reopen", views.DocReopenProject.as_view(), name="document-reopen"),
    # Helper ========================================================
    path("downloadProjectDocument/<int:pk>", views.DownloadProjectDocument.as_view()),
    # Publications ========================================================
    path("publications/<str:employee_id>", views.UserPublications.as_view()),
    path("custompublications", views.CustomPublications.as_view()),
    path("custompublications/<int:pk>", views.CustomPublicationDetail.as_view()),
]
