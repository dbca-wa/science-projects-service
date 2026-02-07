from django.urls import path

from . import views

urlpatterns = [
    # Main - Using "list" instead of "" to avoid trailing slash
    path("list", views.Areas.as_view()),
    path("<int:pk>", views.AreaDetail.as_view()),
    # Sub Types
    path("dbcaregions", views.DBCARegions.as_view()),
    path("dbcadistricts", views.DBCADistricts.as_view()),
    path("ibra", views.Ibras.as_view()),
    path("imcra", views.Imcras.as_view()),
    path("nrm", views.Nrms.as_view()),
]
