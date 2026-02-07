"""
Project utility views
"""

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED
from rest_framework.views import APIView

from documents.models import ProjectDocument
from documents.serializers import ProjectDocumentSerializer

from ..models import Project
from ..serializers import TinyProjectSerializer
from ..services.project_service import ProjectService


class ProjectYears(APIView):
    """Get list of project years"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get unique project years"""
        years = ProjectService.get_project_years()
        return Response(list(years), status=HTTP_200_OK)


class SuspendProject(APIView):
    """Suspend a project"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Suspend project by ID"""
        project = ProjectService.suspend_project(pk, request.user)
        serializer = TinyProjectSerializer(project)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class ProjectDocs(APIView):
    """Get project documents"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get all documents for a project"""
        settings.LOGGER.info(f"{request.user} is viewing documents for project {pk}")

        documents = (
            ProjectDocument.objects.filter(project_id=pk)
            .select_related(
                "project",
                "creator",
                "modifier",
            )
            .order_by("-created_at")
        )

        serializer = ProjectDocumentSerializer(documents, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ToggleUserProfileVisibilityForProject(APIView):
    """Toggle project visibility on user profile"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Toggle visibility"""
        project = ProjectService.toggle_user_profile_visibility(pk, request.user)
        serializer = TinyProjectSerializer(project)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class CoreFunctionProjects(APIView):
    """Get core function projects"""

    def get(self, request):
        """Get all core function projects"""
        projects = Project.objects.filter(kind="core_function").all()
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ScienceProjects(APIView):
    """Get science projects"""

    def get(self, request):
        """Get all science projects"""
        projects = Project.objects.filter(kind="science").all()
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class StudentProjects(APIView):
    """Get student projects"""

    def get(self, request):
        """Get all student projects"""
        projects = Project.objects.filter(kind="student").all()
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ExternalProjects(APIView):
    """Get external projects"""

    def get(self, request):
        """Get all external projects"""
        projects = Project.objects.filter(kind="external").all()
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
