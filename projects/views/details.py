"""
Project details views (ProjectDetail, StudentProjectDetails, ExternalProjectDetails)
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.exceptions import NotFound

from ..models import ProjectDetail
from ..serializers import (
    ProjectDetailSerializer,
    ProjectDetailViewSerializer,
    StudentProjectDetailSerializer,
    TinyStudentProjectDetailSerializer,
    ExternalProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
)
from ..services.details_service import DetailsService


class ProjectAdditional(APIView):
    """List and create project details"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all project details"""
        details = DetailsService.list_all_project_details()
        serializer = ProjectDetailViewSerializer(details, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create project detail"""
        serializer = ProjectDetailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        detail = DetailsService.create_project_details(
            project_id=serializer.validated_data['project'].pk,
            data=serializer.validated_data,
            user=request.user
        )
        
        result_serializer = ProjectDetailViewSerializer(detail)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class ProjectAdditionalDetail(APIView):
    """Get, update, delete project detail"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get project detail by ID"""
        try:
            detail = ProjectDetail.objects.select_related(
                "project",
                "creator",
                "modifier",
                "owner",
            ).get(pk=pk)
        except ProjectDetail.DoesNotExist:
            raise NotFound(f"Project detail {pk} not found")
        
        serializer = ProjectDetailViewSerializer(detail)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update project detail"""
        serializer = ProjectDetailSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        try:
            detail = ProjectDetail.objects.get(pk=pk)
        except ProjectDetail.DoesNotExist:
            raise NotFound(f"Project detail {pk} not found")
        
        settings.LOGGER.info(f"{request.user} is updating project detail {pk}")
        
        # Update fields
        for field, value in serializer.validated_data.items():
            if hasattr(detail, field):
                setattr(detail, field, value)
        
        detail.save()
        
        result_serializer = ProjectDetailViewSerializer(detail)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete project detail"""
        try:
            detail = ProjectDetail.objects.get(pk=pk)
        except ProjectDetail.DoesNotExist:
            raise NotFound(f"Project detail {pk} not found")
        
        settings.LOGGER.info(f"{request.user} is deleting project detail {pk}")
        detail.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class StudentProjectAdditional(APIView):
    """List and create student project details"""
    
    def get(self, request):
        """Get all student project details"""
        details = DetailsService.list_all_student_details()
        serializer = TinyStudentProjectDetailSerializer(details, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create student project detail"""
        serializer = StudentProjectDetailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        detail = DetailsService.create_student_details(
            project_id=serializer.validated_data['project'].pk,
            data=serializer.validated_data,
            user=request.user
        )
        
        result_serializer = TinyStudentProjectDetailSerializer(detail)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class StudentProjectAdditionalDetail(APIView):
    """Get, update, delete student project detail"""
    
    def get(self, request, pk):
        """Get student project detail by ID"""
        detail = DetailsService.get_student_details(pk)
        if not detail:
            raise NotFound(f"Student project detail {pk} not found")
        serializer = TinyStudentProjectDetailSerializer(detail)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update student project detail"""
        serializer = StudentProjectDetailSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Get the detail first to get the project_id
        detail = DetailsService.get_student_details(pk)
        if not detail:
            raise NotFound(f"Student project detail {pk} not found")
        
        detail = DetailsService.update_student_details(
            project_id=detail.project.pk,
            data=serializer.validated_data,
            user=request.user
        )
        
        result_serializer = TinyStudentProjectDetailSerializer(detail)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete student project detail"""
        detail = DetailsService.get_student_details(pk)
        if not detail:
            raise NotFound(f"Student project detail {pk} not found")
        
        settings.LOGGER.info(f"{request.user} is deleting student project detail {pk}")
        detail.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class ExternalProjectAdditional(APIView):
    """List and create external project details"""
    
    def get(self, request):
        """Get all external project details"""
        details = DetailsService.list_all_external_details()
        serializer = TinyExternalProjectDetailSerializer(details, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create external project detail"""
        serializer = ExternalProjectDetailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        detail = DetailsService.create_external_details(
            project_id=serializer.validated_data['project'].pk,
            data=serializer.validated_data,
            user=request.user
        )
        
        result_serializer = TinyExternalProjectDetailSerializer(detail)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class ExternalProjectAdditionalDetail(APIView):
    """Get, update, delete external project detail"""
    
    def get(self, request, pk):
        """Get external project detail by ID"""
        detail = DetailsService.get_external_details(pk)
        if not detail:
            raise NotFound(f"External project detail {pk} not found")
        serializer = TinyExternalProjectDetailSerializer(detail)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update external project detail"""
        serializer = ExternalProjectDetailSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Get the detail first to get the project_id
        detail = DetailsService.get_external_details(pk)
        if not detail:
            raise NotFound(f"External project detail {pk} not found")
        
        detail = DetailsService.update_external_details(
            project_id=detail.project.pk,
            data=serializer.validated_data,
            user=request.user
        )
        
        result_serializer = TinyExternalProjectDetailSerializer(detail)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete external project detail"""
        detail = DetailsService.get_external_details(pk)
        if not detail:
            raise NotFound(f"External project detail {pk} not found")
        
        settings.LOGGER.info(f"{request.user} is deleting external project detail {pk}")
        detail.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class SelectedProjectAdditionalDetail(APIView):
    """Get project detail by project ID"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get project detail for a specific project"""
        detail = DetailsService.get_detail_by_project(pk)
        serializer = ProjectDetailViewSerializer(detail)
        return Response(serializer.data, status=HTTP_200_OK)
