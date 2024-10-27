from . import views
from django.urls import path

urlpatterns = [
    path("", views.AdminControls.as_view()),
    path("<int:pk>", views.AdminControlsDetail.as_view()),
    path("maintainer", views.GetMaintainer.as_view()),
    # Admin Tasks ========================================================
    path("tasks", views.AdminTasks.as_view()),
    path("tasks/pending", views.PendingTasks.as_view()),
    path("tasks/<int:pk>", views.AdminTaskDetail.as_view()),
    # Caretaker ==========================================================
    path("caretakers", views.Caretakers.as_view()),
    path("caretakers/<int:pk>", views.CaretakerDetail.as_view()),
    # Functions on approval of tasks =====================================
    path("tasks/<int:pk>/approve", views.ApproveTask.as_view()),
    path("tasks/<int:pk>/reject", views.RejectTask.as_view()),
    path("tasks/<int:pk>/cancel", views.CancelTask.as_view()),
]
