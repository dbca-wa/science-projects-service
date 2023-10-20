from . import views
from django.urls import path

urlpatterns = [
    path("addresses", views.Addresses.as_view()),
    path("addresses/<int:pk>", views.AddressDetail.as_view()),
    path("users", views.UserContacts.as_view()),
    path("users/<int:pk>", views.UserContactDetail.as_view()),
    path("agencies", views.AgencyContacts.as_view()),
    path("agencies/<int:pk>", views.AgencyContactDetail.as_view()),
    path("branches", views.BranchContacts.as_view()),
    path("branches/<int:pk>", views.BranchContactDetail.as_view()),
]
