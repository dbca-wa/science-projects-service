from django.urls import path
from . import views

urlpatterns = [
    # Caretaker relationships - Using "list" instead of "" to avoid trailing slash
    path("list", views.CaretakerList.as_view(), name="caretaker-list"),
    path("<int:pk>", views.CaretakerDetail.as_view(), name="caretaker-detail"),
    
    # Caretaker requests (AdminTask with action=setcaretaker)
    path("requests", views.CaretakerRequestList.as_view(), name="caretaker-request-list"),  # GET incoming
    path("requests/outgoing", views.CaretakerOutgoingRequestList.as_view(), name="caretaker-outgoing-request-list"),  # GET outgoing
    path("requests/create", views.CaretakerRequestCreate.as_view(), name="caretaker-request-create"),  # POST
    path("requests/<int:pk>/approve", views.ApproveCaretakerRequest.as_view(), name="approve-request"),
    path("requests/<int:pk>/reject", views.RejectCaretakerRequest.as_view(), name="reject-request"),
    path("requests/<int:pk>/cancel", views.CaretakerRequestCancel.as_view(), name="cancel-request"),
    
    # Caretaker tasks
    path("tasks/<int:pk>", views.CaretakerTasksForUser.as_view(), name="caretaker-tasks-user"),
    
    # Caretaker utilities
    path("check", views.CheckCaretaker.as_view(), name="check-caretaker"),
    path("admin-set", views.AdminSetCaretaker.as_view(), name="admin-set-caretaker"),
]
