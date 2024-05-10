from . import views
from django.urls import path

urlpatterns = [
    path("", views.AdminControls.as_view()),
    path("<int:pk>", views.AdminControlsDetail.as_view()),
]
