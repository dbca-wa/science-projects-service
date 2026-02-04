"""
Project closure views
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from ..models import ProjectClosure
from ..serializers import (
    ProjectClosureSerializer,
    TinyProjectClosureSerializer,
)


class ProjectClosures(APIView):
    """List and create project closures"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all project closures"""
        all_project_closures = ProjectClosure.objects.all()
        serializer = TinyProjectClosureSerializer(
            all_project_closures,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create a new project closure"""
        settings.LOGGER.info(f"{request.user} is creating new project closure")
        serializer = ProjectClosureSerializer(data=request.data)
        
        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        project_closure = serializer.save()
        return Response(
            TinyProjectClosureSerializer(project_closure).data,
            status=HTTP_201_CREATED,
        )


class ProjectClosureDetail(APIView):
    """Get, update, and delete project closures"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get project closure by ID"""
        try:
            project_closure = ProjectClosure.objects.get(pk=pk)
        except ProjectClosure.DoesNotExist:
            raise NotFound
        
        serializer = ProjectClosureSerializer(
            project_closure,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update project closure"""
        try:
            project_closure = ProjectClosure.objects.get(pk=pk)
        except ProjectClosure.DoesNotExist:
            raise NotFound
        
        settings.LOGGER.info(
            f"{request.user} is updating project closure {project_closure}"
        )
        
        serializer = ProjectClosureSerializer(
            project_closure,
            data=request.data,
            partial=True,
        )
        
        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        updated_project_closure = serializer.save()
        updated_project_closure.document.modifier = request.user
        updated_project_closure.document.save()
        
        return Response(
            TinyProjectClosureSerializer(updated_project_closure).data,
            status=HTTP_202_ACCEPTED,
        )

    def delete(self, request, pk):
        """Delete project closure"""
        settings.LOGGER.info(f"{request.user} is deleting project closure {pk}")
        
        try:
            project_closure = ProjectClosure.objects.get(pk=pk)
        except ProjectClosure.DoesNotExist:
            raise NotFound
        
        project_closure.delete()
        return Response(status=HTTP_204_NO_CONTENT)
