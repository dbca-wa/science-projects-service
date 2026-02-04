"""
Concept plan views
"""
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from ..serializers import (
    ConceptPlanSerializer,
    ConceptPlanCreateSerializer,
    ConceptPlanUpdateSerializer,
)
from ..services.concept_plan_service import ConceptPlanService
from ..services.document_service import DocumentService
from ..utils.html_tables import json_to_html_table


class ConceptPlans(APIView):
    """List and create concept plans"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List concept plans"""
        # Filter documents by kind
        documents = DocumentService.list_documents(
            user=request.user,
            filters={'kind': 'concept'}
        )
        
        # Get concept plan details
        concept_plans = []
        for doc in documents:
            if hasattr(doc, 'concept_plan_details'):
                details = doc.concept_plan_details.first()
                if details:
                    concept_plans.append(details)
        
        # Serialize
        serializer = ConceptPlanSerializer(
            concept_plans,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'concept_plans': serializer.data
        }, status=HTTP_200_OK)

    def post(self, request):
        """Create concept plan"""
        serializer = ConceptPlanCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Delegate to service
        document = ConceptPlanService.create_concept_plan(
            user=request.user,
            project=serializer.validated_data.get('document').project,
            data=serializer.validated_data
        )
        
        # Get concept plan details
        if hasattr(document, 'concept_plan_details'):
            concept_plan = document.concept_plan_details.first()
            result = ConceptPlanSerializer(concept_plan)
            return Response(result.data, status=HTTP_201_CREATED)
        
        return Response({'error': 'Failed to create concept plan'}, status=HTTP_400_BAD_REQUEST)


class ConceptPlanDetail(APIView):
    """Get, update, and delete concept plans"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get concept plan by ID"""
        document = DocumentService.get_document(pk)
        data = ConceptPlanService.get_concept_plan_data(document)
        
        if 'details' in data:
            serializer = ConceptPlanSerializer(data['details'])
            return Response(serializer.data, status=HTTP_200_OK)
        
        return Response({'error': 'Concept plan not found'}, status=HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """Update concept plan"""
        serializer = ConceptPlanUpdateSerializer(
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Delegate to service
        document = ConceptPlanService.update_concept_plan(
            pk=pk,
            user=request.user,
            data=serializer.validated_data
        )
        
        # Get updated concept plan
        data = ConceptPlanService.get_concept_plan_data(document)
        if 'details' in data:
            result = ConceptPlanSerializer(data['details'])
            return Response(result.data, status=HTTP_200_OK)
        
        return Response({'error': 'Failed to update concept plan'}, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete concept plan"""
        DocumentService.delete_document(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class GetConceptPlanData(APIView):
    """Get concept plan data for PDF generation"""
    
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        Get formatted concept plan data for PDF generation.
        This endpoint processes concept plan data and formats it for document generation.
        """
        import time
        import json
        import datetime
        from operator import attrgetter
        from rest_framework.exceptions import NotFound
        
        from projects.models import ProjectMember
        from medias.models import ProjectPhoto
        from medias.serializers import TinyProjectPhotoSerializer
        from ..models import ConceptPlan
        
        # Get concept plan
        try:
            concept_plan_data = ConceptPlan.objects.get(pk=pk)
        except ConceptPlan.DoesNotExist:
            raise NotFound
        
        # Build document tag
        document_tag = f"CF-{concept_plan_data.project.year}-{concept_plan_data.project.number}"
        project_title = concept_plan_data.project.title
        project_status = concept_plan_data.project.status
        business_area_name = concept_plan_data.project.business_area.name
        
        # Get project team
        members = ProjectMember.objects.filter(project=concept_plan_data.project.pk).all()
        leader = None
        other_members = []
        
        for member in members:
            if member.is_leader:
                leader = member
            else:
                other_members.append(member)
        
        sorted_members = sorted(other_members, key=attrgetter("position"))
        
        team_name_array = []
        if leader:
            team_name_array.append(
                f"{leader.user.display_first_name} {leader.user.display_last_name}"
            )
        
        for member in sorted_members:
            team_name_array.append(
                f"{member.user.display_first_name} {member.user.display_last_name}"
            )
        
        # Get project image
        try:
            image = ProjectPhoto.objects.get(project=concept_plan_data.project.pk)
            project_image = TinyProjectPhotoSerializer(image).data
        except ProjectPhoto.DoesNotExist:
            project_image = None
        
        now = datetime.datetime.now()
        
        # Get approval statuses
        project_lead_approval_granted = concept_plan_data.document.project_lead_approval_granted
        business_area_lead_approval_granted = concept_plan_data.document.business_area_lead_approval_granted
        directorate_approval_granted = concept_plan_data.document.directorate_approval_granted
        
        # Format data using utility function
        background = concept_plan_data.background
        aims = concept_plan_data.aims
        expected_outcomes = concept_plan_data.outcome
        collaborations = concept_plan_data.collaborations
        strategic_context = concept_plan_data.strategic_context
        staff_time_allocation = json_to_html_table(
            concept_plan_data.staff_time_allocation
        )
        indicative_operating_budget = json_to_html_table(
            concept_plan_data.budget
        )
        
        return Response(
            {
                "concept_plan_data_id": concept_plan_data.pk,
                "document_id": concept_plan_data.document.pk,
                "project_id": concept_plan_data.project.pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(team_name_array),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                "background": background,
                "aims": aims,
                "expected_outcomes": expected_outcomes,
                "collaborations": collaborations,
                "strategic_context": strategic_context,
                "staff_time_allocation": staff_time_allocation,
                "indicative_operating_budget": indicative_operating_budget,
            },
            status=HTTP_200_OK,
        )
