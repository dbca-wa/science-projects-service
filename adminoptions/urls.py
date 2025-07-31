from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create a router for ViewSet-based views
router = DefaultRouter()
router.register(r"guide-sections", views.GuideSectionViewSet, basename="guide-sections")
router.register(r"content-fields", views.ContentFieldViewSet, basename="content-fields")

urlpatterns = [
    # Include the router URLs
    path("", include(router.urls)),
    # Your existing URLs
    path("", views.AdminControls.as_view()),
    path("<int:pk>", views.AdminControlsDetail.as_view()),
    # Fixed URL for guide content updates
    path(
        "<int:pk>/update_guide_content/",
        views.AdminControlsGuideContentUpdate.as_view(),
    ),
    path("maintainer", views.GetMaintainer.as_view()),
    # Admin Tasks ========================================================
    path("tasks", views.AdminTasks.as_view()),
    path("tasks/pending", views.PendingTasks.as_view()),
    path("tasks/<int:pk>", views.AdminTaskDetail.as_view()),
    # Caretaker ==========================================================
    path("caretakers", views.Caretakers.as_view()),
    path("caretakers/<int:pk>", views.CaretakerDetail.as_view()),
    path("caretakers/pending/<int:pk>", views.PendingCaretakerTasks.as_view()),
    path("caretakers/requests", views.CheckPendingCaretakerRequestForUser.as_view()),
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
