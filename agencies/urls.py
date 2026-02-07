from django.urls import path

from . import views

urlpatterns = [
    # Main URLS - Using explicit "list" instead of "" to avoid trailing slash on base URL
    path("list", views.Agencies.as_view()),
    # Branches URLS
    path("branches", views.Branches.as_view()),
    path("branches/<int:pk>", views.BranchDetail.as_view()),
    # Business Areas URLS
    path("business_areas", views.BusinessAreas.as_view()),
    path("business_areas/unapproved_docs", views.BusinessAreasUnapprovedDocs.as_view()),
    path(
        "business_areas/problematic_projects",
        views.BusinessAreasProblematicProjects.as_view(),
    ),
    path("business_areas/mine", views.MyBusinessAreas.as_view()),
    path("business_areas/setactive/<int:pk>", views.SetBusinessAreaActive.as_view()),
    path("business_areas/<int:pk>", views.BusinessAreaDetail.as_view()),
    # Affiliations URLS
    path("affiliations", views.Affiliations.as_view()),
    path("affiliations/merge", views.AffiliationsMerge.as_view()),
    path("affiliations/clean_orphaned", views.AffiliationsCleanOrphaned.as_view()),
    path("affiliations/<int:pk>", views.AffiliationDetail.as_view()),
    # Divisions URLS
    path("divisions", views.Divisions.as_view()),
    path("divisions/<int:pk>", views.DivisionDetail.as_view()),
    path("divisions/<int:pk>/email_list", views.DivisionEmailList.as_view()),
    # Services URLS
    path("services", views.DepartmentalServices.as_view()),
    path("services/<int:pk>", views.DepartmentalServiceDetail.as_view()),
    # Agency detail - MUST come last to avoid matching string patterns
    path("<int:pk>", views.AgencyDetail.as_view()),
]
