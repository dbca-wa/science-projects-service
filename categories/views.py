from rest_framework.viewsets import ModelViewSet
from .serializers import ProjectCategorySerializer
from .models import ProjectCategory


class ProjectCategoryViewSet(ModelViewSet):
    serializer_class = ProjectCategorySerializer
    queryset = ProjectCategory.objects.filter(
        kind=ProjectCategory.CategoryKindChoices.SCIENCE,
    )
