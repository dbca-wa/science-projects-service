from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .serializers import ProjectCategorySerializer
from .models import ProjectCategory


class ProjectCategoryViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectCategorySerializer
    queryset = ProjectCategory.objects.filter(
        kind=ProjectCategory.CategoryKindChoices.SCIENCE,
    )
