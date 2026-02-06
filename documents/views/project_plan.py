"""
Project plan views
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

from ..models import ProjectPlan, Endorsement
from ..serializers import (
    ProjectPlanSerializer,
    TinyProjectPlanSerializer,
)


class ProjectPlans(APIView):
    """List and create project plans"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all project plans"""
        all_project_plans = ProjectPlan.objects.all()
        serializer = TinyProjectPlanSerializer(
            all_project_plans,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create a new project plan"""
        settings.LOGGER.info(f"{request.user} is posting a new project plan")
        serializer = ProjectPlanSerializer(data=request.data)
        
        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        project_plan = serializer.save()
        return Response(
            TinyProjectPlanSerializer(project_plan).data,
            status=HTTP_201_CREATED,
        )


class ProjectPlanDetail(APIView):
    """Get, update, and delete project plans"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get project plan by ID"""
        try:
            project_plan = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound
        
        serializer = ProjectPlanSerializer(
            project_plan,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update project plan"""
        settings.LOGGER.info(
            f"{request.user} is updating project plan details for project plan id: {pk}"
        )
        
        try:
            project_plan = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound
        
        # Handle endorsement updates
        if (
            "data_management" in request.data
            or "specimens" in request.data
            or "involves_animals" in request.data
            or "involves_plants" in request.data
        ):
            endorsement_to_edit = Endorsement.objects.filter(project_plan=pk).first()
            
            if endorsement_to_edit:
                if "specimens" in request.data:
                    endorsement_to_edit.no_specimens = request.data["specimens"]

                if "data_management" in request.data:
                    endorsement_to_edit.data_management = request.data["data_management"]

                if "involves_animals" in request.data or "involves_plants" in request.data:
                    involves_animals_value = request.data.get("involves_animals")
                    involves_plants_value = request.data.get("involves_plants")
                    aec_approval_value = request.data.get("ae_endorsement_provided")

                    # Auto set the endorsement to false if it does not involve plants or animals
                    if involves_animals_value:
                        endorsement_to_edit.ae_endorsement_provided = aec_approval_value
                    else:
                        endorsement_to_edit.ae_endorsement_provided = False

                    # Note: There is no hc_endorsement field in the model
                    # Plant endorsement info is stored in no_specimens field

                endorsement_to_edit.save()
        
        # Update project plan
        serializer = ProjectPlanSerializer(
            project_plan,
            data=request.data,
            partial=True,
        )
        
        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        updated_project_plan = serializer.save()
        updated_project_plan.document.modifier = request.user
        updated_project_plan.document.save()

        return Response(
            TinyProjectPlanSerializer(updated_project_plan).data,
            status=HTTP_202_ACCEPTED,
        )

    def delete(self, request, pk):
        """Delete project plan"""
        settings.LOGGER.info(
            f"{request.user} is deleting project plan details for {pk}"
        )
        
        try:
            project_plan = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound
        
        project_plan.delete()
        return Response(status=HTTP_204_NO_CONTENT)
