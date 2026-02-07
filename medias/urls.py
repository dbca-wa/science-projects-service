from django.urls import path

from . import views

urlpatterns = [
    # Reports
    path("report_medias", views.AnnualReportMedias.as_view()),
    path("report_medias/<int:pk>", views.AnnualReportMediaDetail.as_view()),
    path("report_medias/latest/media", views.LatestReportMedia.as_view()),
    path("report_medias/<int:pk>/media", views.AnnualReportMediaUpload.as_view()),
    path(
        "report_medias/<int:pk>/media/<str:section>",
        views.AnnualReportMediaDelete.as_view(),
    ),
    path("report_pdfs", views.AnnualReportPDFs.as_view()),
    path("legacy_report_pdfs", views.LegacyAnnualReportPDFs.as_view()),
    path("report_pdfs/<int:pk>", views.AnnualReportPDFDetail.as_view()),
    path("legacy_report_pdfs/<int:pk>", views.LegacyAnnualReportPDFDetail.as_view()),
    # Business Areas
    path("business_area_photos", views.BusinessAreaPhotos.as_view()),
    path("business_area_photos/<int:pk>", views.BusinessAreaPhotoDetail.as_view()),
    # Projects
    path("project_photos", views.ProjectPhotos.as_view()),
    path("project_photos/<int:pk>", views.ProjectPhotoDetail.as_view()),
    # Project Docs
    path("project_document_pdfs", views.ProjectDocPDFS.as_view()),
    path("methodology_photos", views.MethodologyPhotos.as_view()),
    path("methodology_photos/<int:pk>", views.MethodologyPhotoDetail.as_view()),
    # Agency
    path("agency_photos", views.AgencyPhotos.as_view()),
    path("agency_photos/<int:pk>", views.AgencyPhotoDetail.as_view()),
    # User Avatars
    path("user_avatars", views.UserAvatars.as_view()),
    path("user_avatars/<int:pk>", views.UserAvatarDetail.as_view()),
]
