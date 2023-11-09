from django.urls import path
from . import views

urlpatterns = [
    path("promote", views.PromoteToLeader.as_view()),
    path("", views.Projects.as_view()),
    path("<int:pk>", views.ProjectDetails.as_view()),
    path("<int:pk>/team", views.MembersForProject.as_view()),
    path("<int:pk>/areas", views.AreasForProject.as_view()),
    path("<int:pk>/details", views.SelectedProjectAdditionalDetail.as_view()),
    path("mine", views.MyProjects.as_view()),
    path("smallsearch", views.SmallProjectSearch.as_view()),
    path("research_functions", views.ResearchFunctions.as_view()),
    path("research_functions/<int:pk>", views.ResearchFunctionDetail.as_view()),
    path("project_areas", views.ProjectAreas.as_view()),
    path("project_areas/<int:pk>", views.ProjectAreaDetail.as_view()),
    path("project_members", views.ProjectMembers.as_view()),
    # path("project_members/<int:pk>", views.ProjectMemberDetail.as_view()),
    path(
        "project_members/<int:project_id>/<int:user_id>",
        views.ProjectMemberDetail.as_view(),
    ),
    path(
        "project_members/<int:project_id>/leader", views.ProjectLeaderDetail.as_view()
    ),
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
    # Getters
    path("external", views.ExternalProjects.as_view()),
    path("student", views.StudentProjects.as_view()),
    path("science", views.ScienceProjects.as_view()),
    path("core_function", views.CoreFunctionProjects.as_view()),
    path("download", views.DownloadAllProjectsAsCSV.as_view()),
]
