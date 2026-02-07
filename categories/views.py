from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import ProjectCategory
from .serializers import ProjectCategorySerializer


class ProjectCategoryViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectCategorySerializer
    queryset = ProjectCategory.objects.filter(
        kind=ProjectCategory.CategoryKindChoices.SCIENCE,
    )
