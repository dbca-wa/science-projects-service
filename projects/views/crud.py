"""
Project CRUD views
"""
from math import ceil
from datetime import datetime as dt

from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from common.utils.pagination import paginate_queryset
from ..serializers import (
    CreateProjectSerializer,
    ProjectSerializer,
    ProjectDetailViewSerializer,
    ProjectUpdateSerializer,
    ProjectAreaSerializer,
    ProjectMemberSerializer,
    ProjectDetailSerializer,
    StudentProjectDetailSerializer,
    ExternalProjectDetailSerializer,
)
from ..services.project_service import ProjectService
from ..services.member_service import MemberService
from ..services.details_service import DetailsService
from ..services.area_service import AreaService
from ..permissions.project_permissions import CanEditProject
from medias.models import ProjectPhoto
from medias.serializers import TinyProjectPhotoSerializer
from documents.serializers import (
    ProjectDocumentCreateSerializer,
    ConceptPlanCreateSerializer,
    ProjectPlanCreateSerializer,
)


class Projects(APIView):
    """List and create projects"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List projects with filtering and pagination"""
        # Delegate filtering to service
        projects = ProjectService.list_projects(
            user=request.user,
            filters=request.query_params
        )
        
        # Paginate results
        paginated = paginate_queryset(projects, request)
        
        # Serialize and return
        serializer = ProjectSerializer(
            paginated['items'],
            many=True,
            context={'request': request, 'projects': paginated['items']},
        )
        
        return Response({
            'projects': serializer.data,
            'total_results': paginated['total_results'],
            'total_pages': paginated['total_pages'],
        }, status=HTTP_200_OK)

    def post(self, request):
        """Create a new project"""
        data = request.data
        kind = data.get('kind')
        
        settings.LOGGER.info(f"{request.user} is creating a {kind} project")
        
        # Parse dates
        start_date = None
        end_date = None
        if data.get('startDate'):
            start_date = dt.strptime(data['startDate'], "%Y-%m-%dT%H:%M:%S.%fZ").date()
        if data.get('endDate'):
            end_date = dt.strptime(data['endDate'], "%Y-%m-%dT%H:%M:%S.%fZ").date()
        
        # Parse keywords
        keywords_str = data.get('keywords', '')
        keywords_str = keywords_str.strip('[]').replace('"', '')
        keywords_list = keywords_str.split(',')
        
        # Prepare project data
        project_data = {
            'old_id': 1,
            'kind': kind,
            'status': 'new',
            'year': int(data.get('year')),
            'title': data.get('title'),
            'description': data.get('description', ''),
            'tagline': '',
            'keywords': ','.join(keywords_list),
            'start_date': start_date,
            'end_date': end_date,
            'business_area': data.get('businessArea'),
        }
        
        # Validate project data
        serializer = CreateProjectSerializer(data=project_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Create project with all related data
        with transaction.atomic():
            project = serializer.save()
            
            # Handle project image
            image_data = request.FILES.get('imageData')
            if image_data:
                try:
                    file_path = ProjectService.handle_project_image(image_data)
                    photo = ProjectPhoto.objects.create(
                        file=file_path,
                        uploader=request.user,
                        project=project,
                    )
                except Exception as e:
                    settings.LOGGER.error(f"Image upload error: {e}")
                    return Response(
                        {'error': str(e)},
                        status=HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Create project areas
            location_data_list = data.getlist('locations')
            area_data = {
                'project': project.pk,
                'areas': location_data_list,
            }
            area_serializer = ProjectAreaSerializer(data=area_data)
            if area_serializer.is_valid():
                area_serializer.save()
            else:
                return Response(area_serializer.errors, status=HTTP_400_BAD_REQUEST)
            
            # Add project leader as member
            member_data = {
                'project': project.pk,
                'user': int(data.get('projectLead')),
                'is_leader': True,
                'role': 'supervising',
                'old_id': 1,
            }
            member_serializer = ProjectMemberSerializer(data=member_data)
            if member_serializer.is_valid():
                member_serializer.save()
            else:
                return Response(member_serializer.errors, status=HTTP_400_BAD_REQUEST)
            
            # Create project details
            detail_data = {
                'project': project.pk,
                'creator': data.get('creator'),
                'modifier': data.get('creator'),
                'owner': data.get('creator'),
                'service': data.get('departmentalService'),
                'data_custodian': data.get('dataCustodian'),
            }
            detail_serializer = ProjectDetailSerializer(data=detail_data)
            if detail_serializer.is_valid():
                detail_serializer.save()
            else:
                return Response(detail_serializer.errors, status=HTTP_400_BAD_REQUEST)
            
            # Create kind-specific details
            if kind == 'student':
                student_data = {
                    'project': project.pk,
                    'organisation': data.get('organisation'),
                    'level': data.get('level'),
                    'old_id': 1,
                }
                student_serializer = StudentProjectDetailSerializer(data=student_data)
                if student_serializer.is_valid():
                    student_serializer.save()
                else:
                    return Response(student_serializer.errors, status=HTTP_400_BAD_REQUEST)
            
            elif kind == 'external':
                external_data = {
                    'project': project.pk,
                    'old_id': 1,
                    'description': data.get('externalDescription'),
                    'aims': data.get('aims'),
                    'budget': data.get('budget'),
                    'collaboration_with': data.get('collaborationWith'),
                }
                external_serializer = ExternalProjectDetailSerializer(data=external_data)
                if external_serializer.is_valid():
                    external_serializer.save()
                else:
                    return Response(external_serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Return created project
        result_serializer = ProjectSerializer(project)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class ProjectDetails(APIView):
    """Get, update, and delete a specific project"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get project details"""
        project = ProjectService.get_project(pk)
        serializer = ProjectDetailViewSerializer(project)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update project"""
        self.check_object_permissions(request, ProjectService.get_project(pk))
        
        serializer = ProjectUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        project = ProjectService.update_project(
            pk=pk,
            user=request.user,
            data=serializer.validated_data
        )
        
        result_serializer = ProjectDetailViewSerializer(project)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete project"""
        self.check_object_permissions(request, ProjectService.get_project(pk))
        
        ProjectService.delete_project(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
