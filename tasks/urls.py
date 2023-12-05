from django.urls import path
from . import views

def trigger_error(request):
    division_by_zero = 1 /0

urlpatterns = [
    path("", views.Tasks.as_view()),
    path("feedback", views.Feedbacks.as_view()),
    path("feedback/<int:pk>", views.FeedbackDetail.as_view()),
    path("<int:pk>", views.TaskDetail.as_view()),
    path("mine", views.MyTasks.as_view()),
    path('sentry-debug/', trigger_error),
]
