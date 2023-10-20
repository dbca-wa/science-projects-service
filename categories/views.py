from rest_framework.viewsets import ModelViewSet
from .serializers import ProjectCategorySerializer
from .models import ProjectCategory

# Using ModelViewSet here as shouldn't change much/simple model


class ProjectCategoryViewSet(ModelViewSet):
    serializer_class = ProjectCategorySerializer
    queryset = ProjectCategory.objects.filter(
        kind=ProjectCategory.CategoryKindChoices.SCIENCE,
    )
