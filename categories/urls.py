from django.urls import path
from . import views

urlpatterns = [
    # Using "list" instead of "" to avoid trailing slash
    path(
        "list",
        views.ProjectCategoryViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "<int:pk>",
        views.ProjectCategoryViewSet.as_view(
            {
                "get": "retrieve",
                "put": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
]
