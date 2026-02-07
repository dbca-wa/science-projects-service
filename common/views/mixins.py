"""
View mixins for common functionality
"""

from math import ceil

from django.conf import settings
from rest_framework.response import Response


class SerializerValidationMixin:
    """
    Mixin for consistent serializer validation and saving

    Eliminates repetitive validation code in views
    """

    def validate_and_save(self, serializer_class, data, instance=None, partial=False):
        """
        Validate and save serializer, returning (object, errors)

        Args:
            serializer_class: Serializer class to use
            data: Data to validate
            instance: Existing instance for updates (optional)
            partial: Whether to allow partial updates

        Returns:
            Tuple of (saved_object, errors)
            - If validation succeeds: (object, None)
            - If validation fails: (None, errors_dict)

        Example:
            project, errors = self.validate_and_save(
                ProjectCreateSerializer,
                request.data
            )
            if errors:
                return Response(errors, status=HTTP_400_BAD_REQUEST)
        """
        serializer = serializer_class(instance=instance, data=data, partial=partial)

        if serializer.is_valid():
            return serializer.save(), None

        return None, serializer.errors

    def validate_serializer(self, serializer_class, data, instance=None, partial=False):
        """
        Validate serializer without saving, returning (validated_data, errors)

        Args:
            serializer_class: Serializer class to use
            data: Data to validate
            instance: Existing instance for updates (optional)
            partial: Whether to allow partial updates

        Returns:
            Tuple of (validated_data, errors)
            - If validation succeeds: (validated_data, None)
            - If validation fails: (None, errors_dict)
        """
        serializer = serializer_class(instance=instance, data=data, partial=partial)

        if serializer.is_valid():
            return serializer.validated_data, None

        return None, serializer.errors


class PaginationMixin:
    """
    Mixin for consistent pagination across list views

    Eliminates repetitive pagination code
    """

    def paginate_queryset(self, queryset, request):
        """
        Paginate queryset based on request parameters

        Args:
            queryset: QuerySet to paginate
            request: HTTP request with query parameters

        Returns:
            Dict with pagination data:
            {
                'items': paginated_queryset,
                'total_results': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size,
            }

        Example:
            paginated = self.paginate_queryset(projects, request)
            serializer = ProjectSerializer(paginated['items'], many=True)
            return Response({
                'results': serializer.data,
                'total_results': paginated['total_results'],
                'total_pages': paginated['total_pages'],
            })
        """
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        page_size = getattr(settings, "PAGE_SIZE", 20)

        # Handle custom page_size from request
        try:
            custom_page_size = int(request.query_params.get("page_size", page_size))
            if 1 <= custom_page_size <= 100:  # Limit max page size
                page_size = custom_page_size
        except (ValueError, TypeError):
            pass

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        total_pages = ceil(total_count / page_size) if page_size > 0 else 0

        return {
            "items": queryset[start:end],
            "total_results": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
        }

    def paginated_response(
        self, queryset, serializer_class, request, **serializer_kwargs
    ):
        """
        Create paginated response with serialized data

        Args:
            queryset: QuerySet to paginate and serialize
            serializer_class: Serializer class to use
            request: HTTP request
            **serializer_kwargs: Additional kwargs for serializer

        Returns:
            Response with paginated data

        Example:
            return self.paginated_response(
                projects,
                ProjectSerializer,
                request,
                context={'request': request}
            )
        """
        paginated = self.paginate_queryset(queryset, request)
        serializer = serializer_class(
            paginated["items"], many=True, **serializer_kwargs
        )

        return Response(
            {
                "results": serializer.data,
                "total_results": paginated["total_results"],
                "total_pages": paginated["total_pages"],
                "current_page": paginated["current_page"],
                "page_size": paginated["page_size"],
            }
        )
