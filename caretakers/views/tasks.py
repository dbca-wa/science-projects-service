"""
Views for caretaker task management
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK

from documents.serializers import TinyProjectDocumentSerializerWithUserDocsBelongTo
from ..services import CaretakerTaskService
from ..utils import deduplicate_documents


class CaretakerTasksForUser(APIView):
    """Get tasks for a specific caretakee"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get all pending documents for caretaker user"""
        # Get tasks from service
        task_data = CaretakerTaskService.get_tasks_for_user(pk, request.user)
        
        caretaker_assignments = task_data['caretaker_assignments']
        roles = task_data['roles']
        directorate_documents = task_data['directorate_documents']
        ba_documents = task_data['ba_documents']
        lead_documents = task_data['lead_documents']
        member_documents = task_data['member_documents']
        
        # Serialize directorate documents
        ser_directorate = TinyProjectDocumentSerializerWithUserDocsBelongTo(
            directorate_documents,
            many=True,
            context={"request": request, "for_user": None},
        )
        
        # Serialize BA documents for each BA leader
        ba_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in roles['ba_leader_user_ids']:
                user_ba_areas = assignment.user.business_areas_led.values_list(
                    "id", flat=True
                )
                user_ba_documents = ba_documents.filter(
                    project__business_area__in=user_ba_areas
                )
                
                serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_ba_documents,
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                ba_serialized.extend(serializer.data)
        
        # Serialize lead documents for each project lead
        lead_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in roles['project_lead_user_ids']:
                from projects.models import ProjectMember
                user_lead_projects = ProjectMember.objects.filter(
                    user=assignment.user, is_leader=True
                ).values_list("project_id", flat=True)
                
                user_lead_documents = lead_documents.filter(
                    project__in=user_lead_projects
                )
                
                serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_lead_documents,
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                lead_serialized.extend(serializer.data)
        
        # Serialize team member documents
        member_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in roles['team_member_user_ids']:
                from projects.models import ProjectMember, Project
                active_projects = Project.objects.exclude(status__in=Project.CLOSED_ONLY)
                user_team_projects = ProjectMember.objects.filter(
                    user=assignment.user,
                    is_leader=False,
                    project__in=active_projects
                ).values_list("project_id", flat=True)
                
                user_member_documents = member_documents.filter(
                    project__in=user_team_projects
                )
                
                serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_member_documents,
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                member_serialized.extend(serializer.data)
        
        # Combine and deduplicate
        all_serialized = []
        if directorate_documents:
            all_serialized.extend(ser_directorate.data)
        all_serialized.extend(ba_serialized)
        all_serialized.extend(lead_serialized)
        all_serialized.extend(member_serialized)
        
        data = {
            "all": deduplicate_documents(all_serialized, is_serialized=True),
            "directorate": deduplicate_documents(ser_directorate.data, is_serialized=True),
            "ba": deduplicate_documents(ba_serialized, is_serialized=True),
            "lead": deduplicate_documents(lead_serialized, is_serialized=True),
            "team": deduplicate_documents(member_serialized, is_serialized=True),
        }
        
        return Response(data, status=HTTP_200_OK)
