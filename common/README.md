# Common Backend Utilities

Shared utilities and base classes for consistent backend architecture.

## Structure

```
common/
├── views/          # Base views and mixins
├── serializers/    # Base serializers
├── permissions/    # Common permissions
├── utils/          # Utilities (pagination, filters, validators)
└── models.py       # CommonModel with timestamps
```

## Usage

### Views
```python
from common.views import BaseAPIView, SerializerValidationMixin, PaginationMixin

class ProjectList(BaseAPIView, SerializerValidationMixin, PaginationMixin):
    def get(self, request):
        projects = ProjectService.list_projects(request.user)
        return self.paginated_response(projects, ProjectSerializer, request)
    
    def post(self, request):
        project, errors = self.validate_and_save(ProjectCreateSerializer, request.data)
        if errors:
            return Response(errors, status=HTTP_400_BAD_REQUEST)
        return Response(ProjectSerializer(project).data, status=HTTP_201_CREATED)
```

### Serializers
```python
from common.serializers import BaseModelSerializer, TimestampedSerializer

class ProjectSerializer(BaseModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'status']  # Uses 'id' not 'pk'
```

### Permissions
```python
from common.permissions import IsAdminUser, IsOwnerOrAdmin

class ProjectDetail(BaseAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
```

### Utilities
```python
from common.utils import paginate_queryset, apply_search_filter, validate_not_empty

# Pagination
paginated = paginate_queryset(queryset, request)

# Filtering
queryset = apply_search_filter(queryset, "test", ['title', 'description'])

# Validation
def validate_title(self, value):
    return validate_not_empty(value, "Title")
```
