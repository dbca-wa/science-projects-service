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
    MiniProjectMemberSerializer,
    ProjectDetailSerializer,
    StudentProjectDetailSerializer,
    TinyStudentProjectDetailSerializer,
    ExternalProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
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
            user=request.user, filters=request.query_params
        )

        # Paginate results
        paginated = paginate_queryset(projects, request)

        # Serialize and return
        serializer = ProjectSerializer(
            paginated["items"],
            many=True,
            context={"request": request, "projects": paginated["items"]},
        )

        return Response(
            {
                "projects": serializer.data,
                "total_results": paginated["total_results"],
                "total_pages": paginated["total_pages"],
            },
            status=HTTP_200_OK,
        )

    def post(self, request):
        """Create a new project"""
        data = request.data
        kind = data.get("kind")

        settings.LOGGER.info(f"{request.user} is creating a {kind} project")

        # Parse dates
        start_date = None
        end_date = None
        if data.get("startDate"):
            start_date = dt.strptime(data["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ").date()
        if data.get("endDate"):
            end_date = dt.strptime(data["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ").date()

        # Parse keywords
        keywords_str = data.get("keywords", "")
        keywords_str = keywords_str.strip("[]").replace('"', "")
        keywords_list = keywords_str.split(",")

        # Parse year safely
        year = data.get("year")
        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None

        # Prepare project data
        project_data = {
            "kind": kind,
            "status": "new",
            "year": year,
            "title": data.get("title"),
            "description": data.get("description", ""),
            "tagline": "",
            "keywords": ",".join(keywords_list),
            "start_date": start_date,
            "end_date": end_date,
            "business_area": data.get("businessArea"),
        }

        # Validate project data
        serializer = CreateProjectSerializer(data=project_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        # Create project with all related data
        with transaction.atomic():
            project = serializer.save()

            # Handle project image
            image_data = request.FILES.get("imageData")
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
                        {"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Create project areas
            location_data_list = data.getlist("locations")
            area_data = {
                "project": project.pk,
                "areas": location_data_list,
            }
            area_serializer = ProjectAreaSerializer(data=area_data)
            if area_serializer.is_valid():
                area_serializer.save()
            else:
                return Response(area_serializer.errors, status=HTTP_400_BAD_REQUEST)

            # Add project leader as member
            member_data = {
                "project": project.pk,
                "user": int(data.get("projectLead")),
                "is_leader": True,
                "role": "supervising",
            }
            member_serializer = ProjectMemberSerializer(data=member_data)
            if member_serializer.is_valid():
                member_serializer.save()
            else:
                return Response(member_serializer.errors, status=HTTP_400_BAD_REQUEST)

            # Create project details
            detail_data = {
                "project": project.pk,
                "creator": data.get("creator"),
                "modifier": data.get("creator"),
                "owner": data.get("creator"),
                "service": data.get("departmentalService"),
                "data_custodian": data.get("dataCustodian"),
            }
            detail_serializer = ProjectDetailSerializer(data=detail_data)
            if detail_serializer.is_valid():
                detail_serializer.save()
            else:
                return Response(detail_serializer.errors, status=HTTP_400_BAD_REQUEST)

            # Create kind-specific details
            if kind == "student":
                student_data = {
                    "project": project.pk,
                    "organisation": data.get("organisation"),
                    "level": data.get("level"),
                }
                student_serializer = StudentProjectDetailSerializer(data=student_data)
                if student_serializer.is_valid():
                    student_serializer.save()
                else:
                    return Response(
                        student_serializer.errors, status=HTTP_400_BAD_REQUEST
                    )

            elif kind == "external":
                external_data = {
                    "project": project.pk,
                    "description": data.get("externalDescription"),
                    "aims": data.get("aims"),
                    "budget": data.get("budget"),
                    "collaboration_with": data.get("collaborationWith"),
                }
                external_serializer = ExternalProjectDetailSerializer(
                    data=external_data
                )
                if external_serializer.is_valid():
                    external_serializer.save()
                else:
                    return Response(
                        external_serializer.errors, status=HTTP_400_BAD_REQUEST
                    )

        # Return created project
        result_serializer = ProjectSerializer(project)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class ProjectDetails(APIView):
    """Get, update, and delete a specific project"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get full project details including project, details, documents, and members"""
        from ..models import (
            ProjectDetail,
            StudentProjectDetails,
            ExternalProjectDetails,
            ProjectMember,
        )
        from documents.models import (
            ConceptPlan,
            ProjectPlan,
            ProgressReport,
            StudentReport,
            ProjectClosure,
        )

        # Get project
        project = ProjectService.get_project(pk)
        project_data = ProjectSerializer(project).data

        # Get project details (base)
        try:
            base_detail = ProjectDetail.objects.select_related(
                "creator",
                "modifier",
                "owner",
                "data_custodian",
                "site_custodian",
                "service",
            ).get(project=project)
            base_data = ProjectDetailViewSerializer(base_detail).data
        except ProjectDetail.DoesNotExist:
            base_data = None

        # Get student details if applicable
        try:
            student_detail = StudentProjectDetails.objects.get(project=project)
            student_data = TinyStudentProjectDetailSerializer(student_detail).data
        except StudentProjectDetails.DoesNotExist:
            student_data = []

        # Get external details if applicable
        try:
            external_detail = ExternalProjectDetails.objects.get(project=project)
            external_data = TinyExternalProjectDetailSerializer(external_detail).data
        except ExternalProjectDetails.DoesNotExist:
            external_data = []

        # Get project members
        members = (
            ProjectMember.objects.filter(project=project)
            .select_related(
                "user", "user__profile", "user__work", "user__work__affiliation"
            )
            .prefetch_related("user__caretakers")
            .order_by("position")
        )
        members_data = (
            MiniProjectMemberSerializer(members, many=True).data
            if members.exists()
            else None
        )

        # Get documents
        documents = {
            "concept_plan": None,
            "project_plan": None,
            "progress_reports": [],
            "student_reports": [],
            "project_closure": None,
        }

        # Get concept plan
        try:
            concept_plan = ConceptPlan.objects.select_related("document").get(
                project=project
            )
            documents["concept_plan"] = {
                "id": concept_plan.id,
                "status": concept_plan.document.status,
            }
        except ConceptPlan.DoesNotExist:
            pass

        # Get project plan
        try:
            project_plan = ProjectPlan.objects.select_related("document").get(
                project=project
            )
            documents["project_plan"] = {
                "id": project_plan.id,
                "status": project_plan.document.status,
            }
        except ProjectPlan.DoesNotExist:
            pass

        # Get progress reports
        progress_reports = (
            ProgressReport.objects.filter(project=project)
            .select_related("document")
            .order_by("-year", "-id")
        )
        documents["progress_reports"] = [
            {"id": pr.id, "status": pr.document.status} for pr in progress_reports
        ]

        # Get student reports
        student_reports = (
            StudentReport.objects.filter(project=project)
            .select_related("document")
            .order_by("-id")
        )
        documents["student_reports"] = [
            {"id": sr.id, "status": sr.document.status} for sr in student_reports
        ]

        # Get project closure
        try:
            project_closure = ProjectClosure.objects.select_related("document").get(
                project=project
            )
            documents["project_closure"] = {
                "id": project_closure.id,
                "status": project_closure.document.status,
            }
        except ProjectClosure.DoesNotExist:
            pass

        # Construct full response
        response_data = {
            "project": project_data,
            "details": {
                "base": base_data,
                "external": external_data,
                "student": student_data,
            },
            "documents": documents,
            "members": members_data,
        }

        return Response(response_data, status=HTTP_200_OK)

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAuthenticated(), CanEditProject()]
        return [IsAuthenticated()]

    def put(self, request, pk):
        """Update project"""
        project = ProjectService.get_project(pk)
        self.check_object_permissions(request, project)

        serializer = ProjectUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        project = ProjectService.update_project(
            pk=pk, user=request.user, data=serializer.validated_data
        )

        result_serializer = ProjectSerializer(project)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete project"""
        project = ProjectService.get_project(pk)
        self.check_object_permissions(request, project)

        ProjectService.delete_project(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
