from django.urls import path
from . import views

urlpatterns = [
    # BASE URLS
    path("", views.Projects.as_view()),
    path("<int:pk>", views.ProjectDetails.as_view()),
    path(
        "<int:pk>/toggle_user_profile_visibility",
        views.ToggleUserProfileVisibilityForProject.as_view(),
    ),
    path("map", views.ProjectMap.as_view()),
    path("mine", views.MyProjects.as_view()),
    path("listofyears", views.ProjectYears.as_view()),
    path("smallsearch", views.SmallProjectSearch.as_view()),
    # PROJECT SPECIFIC URLS
    path("<int:pk>/project_docs", views.ProjectDocs.as_view()),
    path("<int:pk>/team", views.MembersForProject.as_view()),
    path("<int:pk>/areas", views.AreasForProject.as_view()),
    path("<int:pk>/details", views.SelectedProjectAdditionalDetail.as_view()),
    path("<int:pk>/suspend", views.SuspendProject.as_view()),
    # PROJECT ASSOCIATED URLS
    path("project_details", views.ProjectAdditional.as_view()),
    path("project_details/<int:pk>", views.ProjectAdditionalDetail.as_view()),
    path("student_project_details", views.StudentProjectAdditional.as_view()),
    path(
        "student_project_details/<int:pk>",
        views.StudentProjectAdditionalDetail.as_view(),
    ),
    path("external_project_details", views.ExternalProjectAdditional.as_view()),
    path(
        "external_project_details/<int:pk>",
        views.ExternalProjectAdditionalDetail.as_view(),
    ),
    # PROJECT TEAM URLS
    path("project_members", views.ProjectMembers.as_view()),
    path(
        "project_members/<int:project_id>/<int:user_id>",
        views.ProjectMemberDetail.as_view(),
    ),
    path(
        "project_members/<int:project_id>/leader", views.ProjectLeaderDetail.as_view()
    ),
    path("promote", views.PromoteToLeader.as_view()),
    # PROJECT AREAS
    path("project_areas", views.ProjectAreas.as_view()),
    path("project_areas/<int:pk>", views.ProjectAreaDetail.as_view()),
    # Getters
    path("external", views.ExternalProjects.as_view()),
    path("student", views.StudentProjects.as_view()),
    path("science", views.ScienceProjects.as_view()),
    path("core_function", views.CoreFunctionProjects.as_view()),
    path("download", views.DownloadAllProjectsAsCSV.as_view()),
    # PROBLEMS
    path("unapprovedFY", views.UnapprovedThisFY.as_view()),
    path("problematic", views.ProblematicProjects.as_view()),
    path("remedy/open_closed", views.RemedyOpenClosed.as_view()),
    path("remedy/memberless", views.RemedyMemberlessProjects.as_view()),
    path("remedy/leaderless", views.RemedyNoLeaderProjects.as_view()),
    path("remedy/multiple_leaders", views.RemedyMultipleLeaderProjects.as_view()),
    path("remedy/external_leaders", views.RemedyExternalLeaderProjects.as_view()),
]
