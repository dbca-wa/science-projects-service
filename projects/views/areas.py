"""
Project area/location management views
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from ..serializers import ProjectAreaSerializer
from ..services.area_service import AreaService


class ProjectAreas(APIView):
    """List and create project areas"""
    
    def get(self, request):
        """Get all project areas"""
        areas = AreaService.list_all_areas()
        serializer = ProjectAreaSerializer(areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create project area"""
        serializer = ProjectAreaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        area = AreaService.create_project_area(
            project_id=serializer.validated_data['project'].pk,
            area_ids=serializer.validated_data.get('areas', []),
            user=request.user
        )
        
        result_serializer = ProjectAreaSerializer(area)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class ProjectAreaDetail(APIView):
    """Get, update, delete project area"""
    
    def get(self, request, pk):
        """Get project area by ID"""
        area = AreaService.get_area_by_pk(pk)
        serializer = ProjectAreaSerializer(area)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update project area"""
        serializer = ProjectAreaSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        area = AreaService.update_area_by_pk(
            pk=pk,
            area_ids=serializer.validated_data.get('areas', []),
            user=request.user
        )
        
        result_serializer = ProjectAreaSerializer(area)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete project area"""
        AreaService.delete_project_area(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class AreasForProject(APIView):
    """Get areas for a specific project"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get areas for project"""
        settings.LOGGER.info(f"{request.user} is viewing areas for project {pk}")
        
        area = AreaService.get_project_area(pk)
        serializer = ProjectAreaSerializer(area)
        return Response(serializer.data, status=HTTP_200_OK)
