from . import views
from django.urls import path

urlpatterns = [
    path("", views.AdminControls.as_view()),
    path("<int:pk>", views.AdminControlsDetail.as_view()),
    path("maintainer", views.GetMaintainer.as_view()),
    # Admin Tasks ========================================================
    path("tasks", views.AdminTasks.as_view()),
    path("tasks/<int:pk>", views.AdminTaskDetail.as_view()),
]
