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
    path("caretakers/pending/<int:pk>", views.PendingCaretakerTasks.as_view()),
    path("caretakers/adminsetcaretaker", views.AdminSetCaretaker.as_view()),
    path("caretakers/checkcaretaker", views.CheckCaretaker.as_view()),
    # Functions on approval of tasks =====================================
    path("tasks/<int:pk>/approve", views.ApproveTask.as_view()),
    path("tasks/<int:pk>/reject", views.RejectTask.as_view()),
    path("tasks/<int:pk>/cancel", views.CancelTask.as_view()),
    # Misc (Admin) ======================================================
    path("mergeusers", views.MergeUsers.as_view()),
    path("caretakers/setcaretaker", views.SetCaretaker.as_view()),
]
