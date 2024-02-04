from django.urls import path
from . import views

urlpatterns = [
    # REST framework
    path("batchapprove", views.BatchApprove.as_view()),
    path("batchapproveold", views.BatchApproveOld.as_view()),
    path("projectdocuments", views.ProjectDocuments.as_view()),
    # path(
    #     "projectdocuments/pendingapproval", views.ProjectDocsPendingApproval.as_view()
    # ),
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
    path("endorsements/pendingmyaction", views.EndorsementsPendingMyAction.as_view()),
    # path("projectdocuments/pendingapproval/reports", views.ReportDocsPendingApproval.as_view()),
    path("projectdocuments/<int:pk>", views.ProjectDocumentDetail.as_view()),
    path("projectdocuments/<int:pk>/comments", views.ProjectDocumentComments.as_view()),
    path("conceptplans", views.ConceptPlans.as_view()),
    path("conceptplans/<int:pk>", views.ConceptPlanDetail.as_view()),
    path("projectplans", views.ProjectPlans.as_view()),
    path("projectplans/<int:pk>", views.ProjectPlanDetail.as_view()),
    path("projectplans/endorsements", views.Endorsements.as_view()),
    path(
        "projectplans/endorsements/<int:pk>",
        views.EndorsementDetail.as_view(),
    ),
    path(
        "project_plans/<int:pk>/seek_endorsement",
        views.SeekEndorsement.as_view(),
    ),
    path("progressreports", views.ProgressReports.as_view()),
    path("progressreports/<int:pk>", views.ProgressReportDetail.as_view()),
    path(
        "progressreports/<int:project>/<int:year>",
        views.ProgressReportByYear.as_view(),
    ),
    path("studentreports", views.StudentReports.as_view()),
    path("studentreports/<int:pk>", views.StudentReportDetail.as_view()),
    path(
        "studentreports/<int:project>/<int:year>",
        views.StudentReportByYear.as_view(),
    ),
    path("projectclosures", views.ProjectClosures.as_view()),
    path("projectclosures/<int:pk>", views.ProjectClosureDetail.as_view()),
    path("projectclosures/reopen/<int:pk>", views.RepoenProject.as_view()),
    path("reports", views.Reports.as_view()),
    path("reports/<int:pk>", views.ReportDetail.as_view()),
    path("publications", views.Publications.as_view()),
    path("publications/<int:pk>", views.PublicationDetail.as_view()),
    # Helper
    path("generateProjectDocument/<int:pk>", views.GenerateProjectDocument.as_view()),
    path("downloadProjectDocument/<int:pk>", views.DownloadProjectDocument.as_view()),
    path("spawn", views.DocumentSpawner.as_view()),
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
    path("reports/completed", views.GetCompletedReports.as_view()),
    path("endorsements", views.ProjectDocuments.as_view()),
    # Actions (PROGRESS REPORT)
    path("actions/approve", views.DocApproval.as_view()),
    path("actions/reopen", views.DocReopenProject.as_view()),
    path("actions/recall", views.DocRecall.as_view()),
    path("actions/send_back", views.DocSendBack.as_view()),
]
