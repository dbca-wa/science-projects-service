from django.urls import path
from . import views

urlpatterns = [
    path("", views.Tasks.as_view()),
    path("<int:pk>", views.TaskDetail.as_view()),
    path("mine", views.MyTasks.as_view()),
]
