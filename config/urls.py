"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/agencies/", include("agencies.urls")),
    # path("api/v1/categories/", include("categories.urls")),
    path("api/v1/contacts/", include("contacts.urls")),
    path("api/v1/communications/", include("communications.urls")),
    path("api/v1/medias/", include("medias.urls")),
    path("api/v1/projects/", include("projects.urls")),
    path("api/v1/documents/", include("documents.urls")),
    path("api/v1/quotes/", include("quotes.urls")),
    path("api/v1/locations/", include("locations.urls")),
    path("api/v1/tasks/", include("tasks.urls")),
] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)
