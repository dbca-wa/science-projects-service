"""
Project search views
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK

from ..serializers import TinyProjectSerializer
from ..services.project_service import ProjectService
from ..services.member_service import MemberService


class SmallProjectSearch(APIView):
    """Small project search for autocomplete"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Search projects with minimal data"""
        projects = ProjectService.list_projects(
            user=request.user,
            filters=request.query_params
        )
        
        # Limit to 20 results for autocomplete
        projects = projects[:20]
        
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class MyProjects(APIView):
    """Get projects for current user"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all projects where user is a member"""
        settings.LOGGER.info(f"{request.user} is viewing their projects")
        
        projects = MemberService.get_user_projects(request.user.pk)
        
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
