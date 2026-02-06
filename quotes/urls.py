from django.urls import path
from . import views

urlpatterns = [
    # Using "list" instead of "" to avoid trailing slash on base URL
    path("list", views.Quotes.as_view()),
    # String patterns MUST come before <int:pk>
    path("create", views.AddQuotesFromUniques.as_view()),
    path("random", views.QuoteRandom.as_view()),
    # Integer pk pattern comes last
    path("<int:pk>", views.QuoteDetail.as_view()),
]
