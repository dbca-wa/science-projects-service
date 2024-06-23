import ast
import json
from rest_framework.exceptions import (
    NotFound,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.db import IntegrityError, transaction
from django.conf import settings
from django.utils import timezone
from math import ceil
from django.db.models import Q, Case, When, Value, F, IntegerField
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
import time
from django.http import HttpResponse
from documents.models import (
    ConceptPlan,
    ProgressReport,
    ProjectClosure,
    ProjectDocument,
    ProjectPlan,
    StudentReport,
)

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os


from documents.serializers import (
    ConceptPlanCreateSerializer,
    ConceptPlanSerializer,
    EndorsementCreationSerializer,
    MidDocumentSerializer,
    ProgressReportSerializer,
    ProjectClosureSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
    ProjectPlanCreateSerializer,
    ProjectPlanSerializer,
    StudentReportSerializer,
    TinyConceptPlanSerializer,
    TinyProgressReportSerializer,
    TinyProjectClosureSerializer,
    TinyProjectDocumentSerializer,
    TinyProjectPlanSerializer,
    TinyStudentReportSerializer,
)
from medias.models import ProjectPhoto
from medias.serializers import TinyProjectPhotoSerializer

from .serializers import (
    CreateProjectSerializer,
    ExternalProjectDetailSerializer,
    ProjectAreaSerializer,
    ProjectDetailSerializer,
    ProjectDetailViewSerializer,
    ProjectSerializer,
    ProjectMemberSerializer,
    ProjectUpdateSerializer,
    # MiniProjectMemberSerializer,
    StudentProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
    TinyProjectDetailSerializer,
    TinyProjectMemberSerializer,
    TinyProjectSerializer,
    # TinyResearchFunctionSerializer,
    # ResearchFunctionSerializer,
    TinyStudentProjectDetailSerializer,
)

from users.models import User
from .models import (
    ExternalProjectDetails,
    Project,
    ProjectDetail,
    ProjectArea,
    ProjectMember,
    # ResearchFunction,
    StudentProjectDetails,
)
import csv

from datetime import datetime as dt

# from rest_framework.pagination import PageNumberPagination


# RESEARCH FUNCTIONS ==========================================================================================


# class ResearchFunctions(APIView):
#     def get(self, req):
#         all = ResearchFunction.objects.all()
#         ser = TinyResearchFunctionSerializer(
#             all,
#             many=True,
#         )
#         return Response(
#             ser.data,
#             status=HTTP_200_OK,
#         )

#     def post(self, req):
#         settings.LOGGER.info(msg=f"{req.user} is creating a research function")
#         ser = ResearchFunctionSerializer(
#             data=req.data,
#         )
#         if ser.is_valid():
#             rf = ser.save()
#             return Response(
#                 TinyResearchFunctionSerializer(rf).data,
#                 status=HTTP_201_CREATED,
#             )
#         else:
#             settings.LOGGER.error(msg=f"{ser.errors}")
#             return Response(
#                 ser.errors,
#                 HTTP_400_BAD_REQUEST,
#             )


# class ResearchFunctionDetail(APIView):
#     def go(self, pk):
#         try:
#             obj = ResearchFunction.objects.get(pk=pk)
#         except ResearchFunction.DoesNotExist:
#             raise NotFound
#         return obj

#     def get(self, req, pk):
#         rf = self.go(pk)
#         ser = ResearchFunctionSerializer(rf)
#         return Response(
#             ser.data,
#             status=HTTP_200_OK,
#         )

#     def delete(self, req, pk):
#         rf = self.go(pk)
#         settings.LOGGER.info(msg=f"{req.user} is deleting research function: {rf}")
#         rf.delete()
#         return Response(
#             status=HTTP_204_NO_CONTENT,
#         )

#     def put(self, req, pk):
#         rf = self.go(pk)
#         settings.LOGGER.info(msg=f"{req.user} is updating research function: {rf}")
#         ser = ResearchFunctionSerializer(
#             rf,
#             data=req.data,
#             partial=True,
#         )
#         if ser.is_valid():
#             urf = ser.save()
#             return Response(
#                 TinyResearchFunctionSerializer(urf).data,
#                 status=HTTP_202_ACCEPTED,
#             )
#         else:
#             settings.LOGGER.error(msg=f"{ser.error}")
#             return Response(
#                 ser.errors,
#                 status=HTTP_400_BAD_REQUEST,
#             )


# PROJECTS =================================================================================================


class SmallProjectSearch(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        page = 1
        page_size = 5
        start = (page - 1) * page_size
        end = start + page_size

        search_term = req.GET.get("searchTerm")

        if req.user.is_superuser:
            projects = Project.objects.all()
        else:
            # Fetch project memberships of the authenticated user (req.user)
            user_memberships = ProjectMember.objects.filter(user=req.user)

            # Get the project IDs from the memberships
            project_ids = user_memberships.values_list("project__id", flat=True)

            # Fetch projects where the user is a member (based on the project IDs)
            projects = Project.objects.filter(id__in=project_ids).order_by("title")

        if search_term:
            # Apply filtering based on the search term
            q_filter = Q(title__icontains=search_term)

            projects = projects.filter(q_filter)

        serialized_projects = TinyProjectSerializer(
            projects[start:end], many=True, context={"request": req}
        ).data

        response_data = {"projects": serialized_projects}

        return Response(response_data, status=HTTP_200_OK)


class MyProjects(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        # Handle not logged in
        if not req.user.is_authenticated:
            return Response(
                {"detail": "You are not logged in."}, status=HTTP_401_UNAUTHORIZED
            )

        # User = get_user_model()

        # Fetch project memberships of the authenticated user (req.user)
        user_memberships = ProjectMember.objects.filter(user=req.user)

        # Get the project IDs from the memberships
        project_ids = user_memberships.values_list("project__id", flat=True)

        # Fetch projects where the user is a member (based on the project IDs)
        active_projects = Project.objects.filter(id__in=project_ids).order_by(
            "-created_at"
        )

        ser = ProjectSerializer(active_projects, many=True)

        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class ProjectYears(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        # Get all unique years from the Project model
        unique_years = Project.objects.values_list("year", flat=True).distinct()

        # Convert the queryset to a list
        year_list = list(unique_years)

        return Response(
            year_list,
            status=HTTP_200_OK,
        )


class Projects(APIView):
    permission_classes = [IsAuthenticated]

    def determine_db_kind(self, provided):
        if provided.startswith("CF"):
            return "core_function"
        elif provided.startswith("STP"):
            return "student"
        elif provided.startswith("SP"):
            return "science"
        elif provided.startswith("EXT"):
            return "external"
        else:
            return None

    def parse_search_term(self, search_term):
        kind = None
        year = None
        number = None

        # Split the search term into parts using '-'
        parts = search_term.split("-")

        # Check if there are at least three parts
        if len(parts) == 3:
            db_kind = self.determine_db_kind(parts[0].upper())
            kind = db_kind
            year = parts[1]
            number = parts[2]

            try:
                year_as_int = int(year)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                projects = Project.objects.filter(kind=kind).all()
                return projects

            if len(year) == 4:
                projects = Project.objects.filter(kind=kind, year=year_as_int).all()
                try:
                    number_as_int = int(number)
                except Exception as e:
                    return projects
                else:
                    number_filter = Q(number__icontains=number_as_int)
                    projects = projects.filter(number_filter)
                    return projects
            else:
                projects = Project.objects.filter(kind=kind, year=year).all()
                return projects

        elif len(parts) == 2:
            year = parts[1]
            db_kind = self.determine_db_kind(parts[0].upper())
            kind = db_kind
            try:
                year_as_int = int(year)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                projects = Project.objects.filter(kind=kind).all()
                return projects
            if len(year) == 4:
                projects = Project.objects.filter(kind=kind, year=year_as_int).all()
            else:
                projects = Project.objects.filter(kind=kind).all()
            return projects

    def get(self, request):
        settings.LOGGER.info(msg=f"{request.user} is viewing/filtering projects")
        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = 12
        start = (page - 1) * page_size
        end = start + page_size

        # Get the values of the checkboxes
        only_active = bool(request.GET.get("only_active", False))
        only_inactive = bool(request.GET.get("only_inactive", False))
        ba_pk = request.GET.get("businessarea", "All")

        # Get the search term
        search_term = request.GET.get("searchTerm")
        # Handle search by project id string
        if search_term and (
            search_term.lower().startswith("cf-")
            or search_term.lower().startswith("sp-")
            or search_term.lower().startswith("stp-")
            or search_term.lower().startswith("ext-")
        ):
            projects = self.parse_search_term(search_term=search_term)

        # Ordinary filtering
        else:
            projects = Project.objects.all()

            if search_term:
                projects = projects.filter(
                    Q(title__icontains=search_term)
                    | Q(description__icontains=search_term)
                    | Q(tagline__icontains=search_term)
                    | Q(keywords__icontains=search_term)
                )

        if ba_pk != "All":
            # print(ba_pk)
            projects = projects.filter(business_area__pk=ba_pk)

        status_slug = request.GET.get("projectstatus", "All")
        if status_slug != "All":
            if status_slug == "unknown":
                projects = projects.exclude(status__in=Project.StatusChoices.values)
            else:
                projects = projects.filter(status=status_slug)

        kind_slug = request.GET.get("projectkind", "All")
        if kind_slug != "All":
            projects = projects.filter(kind=kind_slug)

        year_filter = request.GET.get("year", "All")
        if year_filter != "All":
            projects = projects.filter(year=year_filter)

        # Interaction logic between checkboxes
        if only_active:
            only_inactive = False
        elif only_inactive:
            only_active = False

        # Filter projects based on checkbox values
        if only_active:
            projects = projects.filter(status__in=Project.ACTIVE_ONLY)
        elif only_inactive:
            projects = projects.exclude(status__in=Project.ACTIVE_ONLY)

        total_projects = projects.count()
        total_pages = ceil(total_projects / page_size)

        # Annotate projects to prioritize completed and terminated projects
        # projects = projects.extra(
        #     select={
        #         "custom_ordering": """
        #             CASE
        #                 WHEN status IN ('suspended', 'completed', 'terminated') THEN 1
        #                 ELSE 0
        #             END
        #         """
        #     }
        # ).order_by("custom_ordering", "-year")
        projects = projects.annotate(
            custom_ordering=Case(
                When(
                    status__in=["suspended", "completed", "terminated"], then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by("custom_ordering", "-year", "id")
        projects = projects.distinct()

        serialized_projects = ProjectSerializer(
            projects[start:end],
            many=True,
            context={
                "request": request,
                "projects": projects[start:end],
            },
        )

        response_data = {
            "projects": serialized_projects.data,
            "total_results": total_projects,
            "total_pages": total_pages,
        }

        return Response(response_data, status=HTTP_200_OK)

    def handle_project_image(self, image):
        if isinstance(image, str):
            return image
        elif image is not None:
            # Get the original file name with extension
            original_filename = image.name

            # Specify the subfolder within your media directory
            subfolder = "projects"

            # Combine the subfolder and filename to create the full file path
            file_path = f"{subfolder}/{original_filename}"

            # Check if a file with the same name exists in the subfolder
            if default_storage.exists(file_path):
                # A file with the same name already exists
                full_file_path = default_storage.path(file_path)
                if os.path.exists(full_file_path):
                    existing_file_size = os.path.getsize(full_file_path)
                    new_file_size = (
                        image.size
                    )  # Assuming image.size returns the size of the uploaded file
                    if existing_file_size == new_file_size:
                        # The file with the same name and size already exists, so use the existing file
                        return file_path

            # If the file doesn't exist or has a different size, continue with the file-saving logic
            content = ContentFile(image.read())
            file_path = default_storage.save(file_path, content)

            return file_path

    def post(self, req):
        # DATA WRANGLING =============================================================
        # Get and print the data
        data = req.data
        settings.LOGGER.info(msg=f"{req.user} is creating a {data.get('kind')} project")

        # Extract into individual values for base information
        title = data.get("title")
        description = data.get("description")
        year = int(data.get("year"))
        creator = data.get("creator")
        kind = data.get("kind")
        image_data = req.FILES.get("imageData")
        keywords_str = data.get("keywords")

        is_external = data.get("isExternalSP")

        if is_external:
            if str(is_external).capitalize() == "True":
                is_external = True
            else:
                is_external = False

        # Convert keywords to a string and then list.
        keywords_str = keywords_str.strip("[]").replace('"', "")
        keywords_list = keywords_str.split(",")

        # Extract into individual values for the details
        business_area = data.get("businessArea")
        # research_function = data.get("researchFunction")
        departmental_service = data.get("departmentalService")
        data_custodian = data.get("dataCustodian")
        project_leader = data.get("projectLead")

        start_date_str = data.get("startDate")
        end_date_str = data.get("endDate")

        if start_date_str:
            start_date = dt.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        else:
            start_date = None

        # Check if end_date_str is not None and not empty
        if end_date_str:
            end_date = dt.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        else:
            end_date = None

        # Individual values (location)
        location_data_list = data.getlist("locations")
        status = "new"

        # OBJECT CREATION =============================================================
        # Create base project object & serialize
        project_data_object = {
            "old_id": 1,
            "kind": kind,
            "status": status,
            "year": year,
            "title": title,
            "description": description,
            "tagline": "",
            "keywords": ",".join(keywords_list),
            "start_date": start_date,
            "end_date": end_date,
            "business_area": business_area,
        }

        ser = CreateProjectSerializer(data=project_data_object)
        if ser.is_valid():
            with transaction.atomic():
                proj = ser.save()
                project_id = proj.pk

                # Prep and create the project image, if an image was sent
                if image_data:
                    try:
                        image_data = {
                            "file": self.handle_project_image(image_data),
                            "uploader": req.user,
                            "project": proj,
                        }
                    except ValueError as e:
                        settings.LOGGER.error(msg=f"{e}")
                        error_message = str(e)
                        response_data = {"error": error_message}
                        return Response(response_data, status=HTTP_400_BAD_REQUEST)

                    try:
                        new_proj_photo_instance = ProjectPhoto.objects.create(
                            **image_data
                        )
                        response = TinyProjectPhotoSerializer(
                            new_proj_photo_instance
                        ).data
                    except Exception as e:
                        settings.LOGGER.error(msg=f"{e}")
                        response_data = {"error": str(e)}
                        return Response(
                            response_data, status=HTTP_500_INTERNAL_SERVER_ERROR
                        )

                # Prep and create the areas of the project
                project_area_data_object = {
                    "project": project_id,
                    "areas": location_data_list,
                }
                project_area_ser = ProjectAreaSerializer(data=project_area_data_object)
                if project_area_ser.is_valid():
                    try:
                        project_area_ser.save()
                    except Exception as e:
                        settings.LOGGER.error(msg=f"{e}")
                        response_data = {"error": str(e)}
                        return Response(
                            response_data,
                            HTTP_400_BAD_REQUEST,
                        )
                else:
                    settings.LOGGER.error(msg=f"{project_area_ser.errors}")
                    return Response(
                        project_area_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # Create an entry for project members
                project_member_data_object = {
                    "project": project_id,
                    "user": int(project_leader),
                    "is_leader": True,
                    "role": "supervising",  # if kind == "student" else "research"
                    "old_id": 1,
                }
                project_member_ser = ProjectMemberSerializer(
                    data=project_member_data_object
                )
                if project_member_ser.is_valid():
                    try:
                        project_member_ser.save()
                    except IntegrityError as e:
                        settings.LOGGER.error(msg=f"{e}")
                        return Response(
                            "An identical user already exists on this project",
                            HTTP_400_BAD_REQUEST,
                        )

                    except Exception as e:
                        settings.LOGGER.error(msg=f"{e}")
                else:
                    settings.LOGGER.error(msg=f"{project_member_ser.errors}")
                    return Response(
                        project_member_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # TODO: Seek guidance on whether a data custodian role should be created as a team member

                # Create an entry for project details
                project_detail_data_object = {
                    "project": project_id,
                    "creator": creator,
                    "modifier": creator,
                    "owner": creator,
                    "service": departmental_service,
                    "data_custodian": data_custodian,
                    # site_custodian:,
                    # "research_function": research_function,
                }

                project_detail_ser = ProjectDetailSerializer(
                    data=project_detail_data_object
                )
                if project_detail_ser.is_valid():
                    # with transaction.atomic():
                    try:
                        project_detail_ser.save()
                    except Exception as e:
                        settings.LOGGER.error(msg=f"{e}")
                        return Response(
                            e,
                            HTTP_400_BAD_REQUEST,
                        )
                else:
                    settings.LOGGER.error(msg=f"{project_detail_ser.errors}")
                    return Response(
                        project_detail_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # Create unique entries in student table if student project
                if kind == "student":
                    level = data.get("level")
                    organisation = data.get("organisation")
                    old_id = 1

                    # Create the object
                    student_project_details_data_object = {
                        "project": project_id,
                        "organisation": organisation,
                        "level": level,
                        "old_id": old_id,
                    }

                    student_proj_details_ser = StudentProjectDetailSerializer(
                        data=student_project_details_data_object
                    )
                    if student_proj_details_ser.is_valid():
                        try:
                            student_proj_details_ser.save()
                        except Exception as e:
                            settings.LOGGER.error(msg=f"{e}")
                    else:
                        settings.LOGGER.error(msg=f"{student_proj_details_ser.errors}")
                        return Response(
                            student_proj_details_ser.errors,
                            HTTP_400_BAD_REQUEST,
                        )

                # Create unique entries in external table if external project
                elif kind == "external":
                    old_id = 1
                    externalDescription = data.get("externalDescription")
                    aims = data.get("aims")
                    budget = data.get("budget")
                    collaboration_with = data.get("collaborationWith")

                    # Create the object
                    external_details_data_object = {
                        "project": project_id,
                        "old_id": old_id,
                        "description": externalDescription,
                        "aims": aims,
                        "budget": budget,
                        "collaboration_with": collaboration_with,
                    }

                    external_details_ser = ExternalProjectDetailSerializer(
                        data=external_details_data_object
                    )
                    if external_details_ser.is_valid():
                        # with transaction.atomic():
                        try:
                            external_details_ser.save()
                        except Exception as e:
                            settings.LOGGER.error(msg=f"{e}")
                    else:
                        settings.LOGGER.error(external_details_ser.errors)
                        return Response(
                            HTTP_400_BAD_REQUEST,
                        )
                # if kind != "student" and kind != "external"
                else:
                    # serialized_proj = ProjectSerializer(proj)

                    # create document for concept plan or project plan
                    document_serializer = ProjectDocumentCreateSerializer(
                        data={
                            "old_id": 1,
                            "kind": "concept" if not is_external else "projectplan",
                            "status": "new",
                            "project": proj.pk,
                            "creator": req.user.pk,
                            "modifier": req.user.pk,
                        }
                    )

                    if document_serializer.is_valid():
                        with transaction.atomic():
                            try:
                                doc = document_serializer.save()
                            except Exception as e:
                                settings.LOGGER.error(msg=f"{e}")
                                return Response(
                                    e,
                                    status=HTTP_400_BAD_REQUEST,
                                )

                            if not is_external:
                                concept_plan_data_object = {
                                    "document": doc.pk,
                                    "project": proj.pk,
                                    "aims": (
                                        req.data.get("aims")
                                        if req.data.get("aims") is not None
                                        else "<p></p>"
                                    ),
                                    "outcome": (
                                        req.data.get("outcome")
                                        if req.data.get("outcome") is not None
                                        else "<p></p>"
                                    ),
                                    "collaborations": (
                                        req.data.get("collaborations")
                                        if req.data.get("collaborations") is not None
                                        else "<p></p>"
                                    ),
                                    "strategic_context": (
                                        req.data.get("strategic_context")
                                        if req.data.get("strategic_context") is not None
                                        else "<p></p>"
                                    ),
                                    "staff_time_allocation": (
                                        req.data.get("staff_time_allocation")
                                        if req.data.get("staff_time_allocation")
                                        is not None
                                        else '<table class="table-light">\
                                            <colgroup>\
                                                <col>\
                                                <col>\
                                                <col>\
                                                <col>\
                                            </colgroup>\
                                            <tbody>\
                                                <tr>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Role</span>\
                                                    </p>\
                                                </th>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Year 1</span>\
                                                    </p>\
                                                </th>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Year 2</span>\
                                                    </p>\
                                                </th>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Year 3</span>\
                                                    </p>\
                                                </th>\
                                                </tr>\
                                                <tr>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Scientist</span>\
                                                    </p>\
                                                </th>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                </tr>\
                                                <tr>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Technical</span>\
                                                    </p>\
                                                </th>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                </tr>\
                                                <tr>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Volunteer</span>\
                                                    </p>\
                                                </th>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                </tr>\
                                                <tr>\
                                                <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                    <p class="editor-p-light" dir="ltr">\
                                                    <span style="white-space: pre-wrap;">Collaborator</span>\
                                                    </p>\
                                                </th>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                </tr>\
                                            </tbody>\
                                            </table>'
                                    ),
                                    "budget": (
                                        req.data.get("budget")
                                        if req.data.get("budget") is not None
                                        else '<table class="table-light"><colgroup>\
                                    <col>\
                                    <col>\
                                    <col>\
                                    <col>\
                                </colgroup>\
                                <tbody>\
                                    <tr>\
                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                        <p class="editor-p-light" dir="ltr">\
                                        <span style="white-space: pre-wrap;">Source</span>\
                                        </p>\
                                    </th>\
                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                        <p class="editor-p-light" dir="ltr">\
                                        <span style="white-space: pre-wrap;">Year 1</span>\
                                        </p>\
                                    </th>\
                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                        <p class="editor-p-light" dir="ltr">\
                                        <span style="white-space: pre-wrap;">Year 2</span>\
                                        </p>\
                                    </th>\
                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                        <p class="editor-p-light" dir="ltr">\
                                        <span style="white-space: pre-wrap;">Year 3</span>\
                                        </p>\
                                    </th>\
                                    </tr>\
                                    <tr>\
                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                        <p class="editor-p-light" dir="ltr">\
                                        <span style="white-space: pre-wrap;">Consolidated Funds (DBCA)</span>\
                                        </p>\
                                    </th>\
                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                    </tr>\
                                    <tr>\
                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                        <p class="editor-p-light" dir="ltr">\
                                        <span style="white-space: pre-wrap;">External Funding</span>\
                                        </p>\
                                    </th>\
                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                    </tr>\
                                </tbody>\
                                </table>'
                                    ),
                                }

                                concept_plan_serializer = ConceptPlanCreateSerializer(
                                    data=concept_plan_data_object
                                )

                                if concept_plan_serializer.is_valid():
                                    try:
                                        concept_plan_serializer.save()
                                    except Exception as e:
                                        settings.LOGGER.error(
                                            msg=f"Concept Plan Error: {e}"
                                        )
                                        return Response(
                                            e,
                                            status=HTTP_400_BAD_REQUEST,
                                        )
                                else:
                                    settings.LOGGER.error(
                                        msg=f"Concept Plan Error: {concept_plan_serializer.errors}"
                                    )
                                    return Response(
                                        concept_plan_serializer.errors,
                                        status=HTTP_400_BAD_REQUEST,
                                    )
                            else:
                                # if external sp
                                project_plan_data_object = {
                                    "document": doc.pk,
                                    "project": proj.pk,
                                    "background": (
                                        req.data.get("background")
                                        if req.data.get("background") is not None
                                        else "<p></p>"
                                    ),
                                    "aims": (
                                        req.data.get("aims")
                                        if req.data.get("aims") is not None
                                        else "<p></p>"
                                    ),
                                    "outcome": (
                                        req.data.get("outcomes")
                                        if req.data.get("outcomes") is not None
                                        else "<p></p>"
                                    ),
                                    "project_tasks": (
                                        req.data.get("project_tasks")
                                        if req.data.get("project_tasks") is not None
                                        else "<p></p>"
                                    ),
                                    "knowledge_transfer": (
                                        req.data.get("knowledge_transfer")
                                        if req.data.get("knowledge_transfer")
                                        is not None
                                        else "<p></p>"
                                    ),
                                    "listed_references": (
                                        req.data.get("references")
                                        if req.data.get("references") is not None
                                        else "<p></p>"
                                    ),
                                    "methodology": (
                                        req.data.get("methodology")
                                        if req.data.get("methodology") is not None
                                        else "<p></p>"
                                    ),
                                    "methodology": (
                                        req.data.get("methodology")
                                        if req.data.get("methodology") is not None
                                        else "<p></p>"
                                    ),
                                    "operating_budget": (
                                        req.data.get("budget")
                                        if req.data.get("budget") is not None
                                        else '<table class="table-light">\
                                                <colgroup>\
                                                    <col>\
                                                    <col>\
                                                    <col>\
                                                    <col>\
                                                </colgroup>\
                                                <tbody>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Source</span>\
                                                        </p>\
                                                    </th>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Year 1</span>\
                                                        </p>\
                                                    </th>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Year 2</span>\
                                                        </p>\
                                                    </th>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Year 3</span>\
                                                        </p>\
                                                    </th>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">FTE Scientist</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">FTE Technical</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Equipment</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Vehicle</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Travel</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Other</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                    <tr>\
                                                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                        <p class="editor-p-light" dir="ltr">\
                                                        <span style="white-space: pre-wrap;">Total</span>\
                                                        </p>\
                                                    </th>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                                    </tr>\
                                                </tbody>\
                                                </table>'
                                    ),
                                    "operating_external_budget": (
                                        req.data.get("budget")
                                        if req.data.get("budget") is not None
                                        else '<table class="table-light">\
                                        <colgroup>\
                                            <col>\
                                            <col>\
                                            <col>\
                                            <col>\
                                        </colgroup>\
                                        <tbody>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Source</span>\
                                                </p>\
                                            </th>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Year 1</span>\
                                                </p>\
                                            </th>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Year 2</span>\
                                                </p>\
                                            </th>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Year 3</span>\
                                                </p>\
                                            </th>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Salaries, Wages, Overtime</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Overheads</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Equipment</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Vehicle</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Travel</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Other</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                            <tr>\
                                            <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
                                                <p class="editor-p-light" dir="ltr">\
                                                <span style="white-space: pre-wrap;">Total</span>\
                                                </p>\
                                            </th>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
                                            </tr>\
                                        </tbody>\
                                        </table>'
                                    ),
                                    "related_projects": "<p></p>",
                                }

                                project_plan_serializer = ProjectPlanCreateSerializer(
                                    data=project_plan_data_object,
                                )

                                if project_plan_serializer.is_valid():
                                    try:
                                        updated = project_plan_serializer.save()
                                    except Exception as e:
                                        settings.LOGGER.error(
                                            msg=f"Project Plan Error: {e}"
                                        )
                                        return Response(
                                            e,
                                            status=HTTP_400_BAD_REQUEST,
                                        )
                                    else:
                                        # Create the endorsement
                                        endorsements = EndorsementCreationSerializer(
                                            data={
                                                "project_plan": updated.pk,
                                                # "bm_endorsement_required": True,
                                                # "hc_endorsement_required": False,
                                                # "dm_endorsement_required": True,
                                                "ae_endorsement_required": False,
                                                # "bm_endorsement_provided": False,
                                                # "hc_endorsement_provided": False,
                                                "ae_endorsement_provided": False,
                                                # "dm_endorsement_provided": False,
                                                "data_management": "<p></p>",
                                                "no_specimens": "<p></p>",
                                            }
                                        )
                                    if endorsements.is_valid():
                                        endorsements.save()

                                    else:
                                        settings.LOGGER.error(
                                            f"endorsement error: {endorsements.errors}"
                                        )
                                        return Response(
                                            endorsements.errors,
                                            HTTP_400_BAD_REQUEST,
                                        )

                                else:
                                    settings.LOGGER.error(
                                        msg=f"Project Plan Error: {project_plan_serializer.errors}"
                                    )
                                    return Response(
                                        project_plan_serializer.errors,
                                        status=HTTP_400_BAD_REQUEST,
                                    )

                    else:
                        settings.LOGGER.error(
                            msg=f"Document Creation Error: {document_serializer.errors}"
                        )
                        return Response(
                            document_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyProjectSerializer(proj).data,
                    status=HTTP_201_CREATED,
                )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class SuspendProject(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        proj = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is trying to suspend a project (pk {pk}): \n{proj.title}"
        )
        try:
            current_status = proj.status
            if current_status != Project.StatusChoices.SUSPENDED:
                proj.status = Project.StatusChoices.SUSPENDED
            else:
                proj.status = Project.StatusChoices.ACTIVE
            proj.save()
            return Response(
                data={"ok": "Project Suspension updated"}, status=HTTP_202_ACCEPTED
            )
        except Exception as e:
            return Response(data={"error": f"{e}"}, status=HTTP_400_BAD_REQUEST)


class ProjectDetails(APIView):
    def go(self, pk):
        try:
            obj = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            raise NotFound
        return obj

    def get_full_object(self, pk):
        try:
            obj = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            raise NotFound
        else:
            base_details = ProjectDetail.objects.get(project=obj)

        try:
            student_details = StudentProjectDetails.objects.get(project=obj)
        except StudentProjectDetails.DoesNotExist:
            student_details = []
        try:
            external_details = ExternalProjectDetails.objects.get(project=obj)
        except ExternalProjectDetails.DoesNotExist:
            external_details = []

        details = {
            "base": ProjectDetailViewSerializer(
                base_details,
            ).data,
            "student": (
                StudentProjectDetailSerializer(
                    student_details,
                ).data
                if student_details != []
                else []
            ),
            "external": (
                ExternalProjectDetailSerializer(
                    external_details,
                ).data
                if external_details != []
                else []
            ),
        }

        try:
            concept_plan = ConceptPlan.objects.get(document__project=obj)
        except ConceptPlan.DoesNotExist:
            concept_plan = None
        try:
            project_plan = ProjectPlan.objects.get(document__project=obj)
        except ProjectPlan.DoesNotExist:
            project_plan = None
        try:
            progress_reports = ProgressReport.objects.filter(
                document__project=obj
            ).all()
        except ProgressReport.DoesNotExist:
            progress_reports = None
        try:
            student_reports = StudentReport.objects.filter(document__project=obj).all()
        except StudentReport.DoesNotExist:
            student_reports = None
        try:
            project_closure = ProjectClosure.objects.get(document__project=obj)
        except ProjectClosure.DoesNotExist:
            project_closure = None

        documents = {
            "concept_plan": (
                ConceptPlanSerializer(concept_plan).data
                if concept_plan != None
                else None
            ),
            "project_plan": (
                ProjectPlanSerializer(project_plan).data
                if project_plan != None
                else None
            ),
            "progress_reports": (
                ProgressReportSerializer(progress_reports, many=True).data
                if progress_reports != None
                else None
            ),
            "student_reports": (
                StudentReportSerializer(student_reports, many=True).data
                if student_reports != None
                else None
            ),
            "project_closure": (
                ProjectClosureSerializer(project_closure).data
                if project_closure != None
                else None
            ),
        }

        try:
            project_members = ProjectMember.objects.filter(project=obj)
        except ProjectMember.DoesNotExist:
            project_members = None

        members = (
            TinyProjectMemberSerializer(project_members, many=True).data
            if project_members != None
            else None
        )

        try:
            project_areas = ProjectArea.objects.get(project=obj)
        except ProjectArea.DoesNotExist:
            project_areas = None

        area_obj = (
            ProjectAreaSerializer(project_areas).data if project_areas != None else None
        )

        return details, documents, members, area_obj

    def get(self, req, pk):
        # print("GETTING PROJECT DETAILS...")
        proj = self.go(pk=pk)
        settings.LOGGER.info(msg=f"{req.user} is viewing project: {proj}")
        ser = ProjectSerializer(proj).data
        # print("SER...")
        details, documents, members, area_obj = self.get_full_object(pk)
        # print("FULL OBJ")
        # data = {
        #     "project": ser,
        #     "details": details,
        #     "documents": documents,
        #     "members": members,
        #     "location": area_obj,
        # }
        # try:
        #     json_str = json.dumps(documents["progress_reports"], indent=4)
        #     print(json_str)
        # except Exception as e:
        #     print(f"\n\nERROR IS HERE: {e}\n\n")

        return Response(
            {
                "project": ser,
                "details": details,
                "documents": documents,
                "members": members,
                "location": area_obj,
            },
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        proj = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting project: {proj}")
        proj.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def handle_project_image(self, image):
        if isinstance(image, str):
            return image
        elif image is not None:
            # Get the original file name with extension
            original_filename = image.name

            # Specify the subfolder within your media directory
            subfolder = "projects"

            # Combine the subfolder and filename to create the full file path
            file_path = f"{subfolder}/{original_filename}"

            # Check if a file with the same name exists in the subfolder
            if default_storage.exists(file_path):
                # A file with the same name already exists
                full_file_path = default_storage.path(file_path)
                if os.path.exists(full_file_path):
                    existing_file_size = os.path.getsize(full_file_path)
                    new_file_size = (
                        image.size
                    )  # Assuming image.size returns the size of the uploaded file
                    if existing_file_size == new_file_size:
                        # The file with the same name and size already exists, so use the existing file
                        return file_path

            # If the file doesn't exist or has a different size, continue with the file-saving logic
            content = ContentFile(image.read())
            file_path = default_storage.save(file_path, content)
            # `file_path` now contains the path to the saved file

            return file_path

    def put(self, req, pk):
        proj = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating project: {proj}")
        title = req.data.get("title")
        description = req.data.get("description")
        image = req.data.get("image")
        status = req.data.get("status")
        data_custodian = req.data.get("data_custodian")

        keywords = req.data.get("keywords")
        locations_str = req.data.get("locations")

        start_date_str = req.data.get("startDate")
        end_date_str = req.data.get("endDate")

        service = req.data.get("service")
        # research_function = req.data.get("research_function")
        business_area = req.data.get("businessArea")
        # print(business_area)

        # Check if start_date_str is not None and not empty
        if start_date_str:
            start_date = dt.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        else:
            start_date = None

        # Check if end_date_str is not None and not empty
        if end_date_str:
            end_date = dt.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        else:
            end_date = None

        # print(proj)

        updated_base_proj_data = {
            key: value
            for key, value in {
                "title": title,
                "description": description,
                "keywords": keywords,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
        }

        # Add business_area separately if it's not None / skip it if error
        if business_area is not None:
            try:
                updated_base_proj_data["business_area"] = int(business_area)
            except Exception as e:
                settings.LOGGER.error(msg=f"BA not convertable to int: {business_area}")
                pass

        print(updated_base_proj_data)

        updated_proj_detail_data = {
            key: value
            for key, value in {
                # "research_function": research_function,
                "service": service,
                "data_custodian": data_custodian,
                "modifier": req.user.pk,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
        }

        # External Fields
        collaboration_with = req.data.get("collaborationWith")
        budget = req.data.get("budget")
        external_description = req.data.get("externalDescription")
        aims = req.data.get("aims")

        # Student Fields
        level = req.data.get("level")
        organisation = req.data.get("organisation")

        updated_student_project_data = {
            key: value
            for key, value in {
                "level": level,
                "organisation": organisation,
            }.items()
            if level is not None
            and organisation is not None
            and (not isinstance(value, list) or value)
        }

        updated_external_project_data = {
            key: value
            for key, value in {
                "description": external_description,
                "aims": aims,
                "budget": budget,
                "collaboration_with": collaboration_with,
            }.items()
            if aims is not None
            and external_description is not None
            and budget is not None
            and collaboration_with is not None
            and (not isinstance(value, list) or value)
        }

        if locations_str and locations_str != "[]":
            updated_proj_area_data = {
                key: value
                for key, value in {
                    "areas": json.loads(locations_str),
                }.items()
                if value is not None and (not isinstance(value, list) or value)
            }
        else:
            # check if there is a project plan matching project
            projplan = ProjectPlan.objects.filter(project=pk).first()

            # if there is, if the document has project lead approval,
            # it cant be set to empty, do not update
            if projplan and projplan.document.project_lead_approval_granted:
                updated_proj_area_data = {}

            else:
                # Otherwise, set empty
                updated_proj_area_data = {"areas": []}

        updated_proj_image_data = {
            key: value
            for key, value in {
                "file": image,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
        }

        base_ser = ProjectUpdateSerializer(
            proj,
            data=updated_base_proj_data,
            partial=True,
        )

        if base_ser.is_valid():
            # print("BASE SER IS VALID")
            # print(base_ser)
            with transaction.atomic():
                # Create the image or update the file if an image is present
                uproj = base_ser.save()

                if updated_proj_detail_data:
                    project_details = ProjectDetail.objects.get(project=proj)
                    detail_ser = ProjectDetailSerializer(
                        project_details,
                        data=updated_proj_detail_data,
                        partial=True,
                    )
                    if detail_ser.is_valid():
                        detail_ser.save()
                    else:
                        settings.LOGGER.error(msg=f"{detail_ser.errors}")
                        return Response(
                            detail_ser.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )
                if updated_proj_image_data:
                    # Check if project already has an image:
                    try:
                        project_photo = ProjectPhoto.objects.get(project=pk)
                    except ProjectPhoto.DoesNotExist as e:
                        settings.LOGGER.warning(
                            msg=f"{req.user} is creating new Project Photo instance as one does not exist for Project ID: {pk}"
                        )
                        # Create the object with the data
                        try:
                            image_data = {
                                "file": self.handle_project_image(image),
                                "uploader": req.user,
                                "project": proj,
                            }
                        except ValueError as e:
                            settings.LOGGER.error(msg=f"{e}")
                            error_message = str(e)
                            response_data = {"error": error_message}
                            return Response(response_data, status=HTTP_400_BAD_REQUEST)

                        try:
                            new_proj_photo_instance = ProjectPhoto.objects.create(
                                **image_data
                            )
                            response = TinyProjectPhotoSerializer(
                                new_proj_photo_instance
                            ).data
                        except Exception as e:
                            settings.LOGGER.error(msg=f"{e}")
                            response_data = {"error": str(e)}
                            return Response(
                                response_data, status=HTTP_500_INTERNAL_SERVER_ERROR
                            )
                    #
                    else:
                        # project_photo.file = self.handle_project_image(image_data)
                        img_ser = TinyProjectPhotoSerializer(
                            project_photo,
                            data=updated_proj_image_data,
                            partial=True,
                        )
                        if img_ser.is_valid():
                            img_ser.save()
                        else:
                            settings.LOGGER.error(msg=f"{img_ser.errors}")
                            return Response(
                                img_ser.errors,
                                status=HTTP_400_BAD_REQUEST,
                            )
                else:
                    selectedImageUrl = req.data.get("selectedImageUrl")
                    if selectedImageUrl == "delete":
                        project_photo = ProjectPhoto.objects.filter(project=pk).first()
                        if project_photo:
                            project_photo.delete()

                if updated_proj_area_data:
                    project_area = ProjectArea.objects.get(project=proj)
                    area_ser = ProjectAreaSerializer(
                        project_area,
                        data=updated_proj_area_data,
                        partial=True,
                    )
                    if area_ser.is_valid():
                        area_ser.save()
                    else:
                        settings.LOGGER.error(msg=f"{area_ser.errors}")
                        return Response(
                            area_ser.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                if updated_external_project_data:
                    project_details = ExternalProjectDetails.objects.get(project=proj)
                    external_ser = ExternalProjectDetailSerializer(
                        project_details,
                        data=updated_external_project_data,
                        partial=True,
                    )
                    if external_ser.is_valid():
                        external_ser.save()
                    else:
                        settings.LOGGER.error(msg=f"{external_ser.errors}")
                        return Response(
                            external_ser.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                if updated_student_project_data:
                    project_details = StudentProjectDetails.objects.get(project=proj)
                    student_proj_detail_ser = StudentProjectDetailSerializer(
                        project_details,
                        data=updated_student_project_data,
                        partial=True,
                    )
                    if student_proj_detail_ser.is_valid():
                        student_proj_detail_ser.save()
                    else:
                        settings.LOGGER.error(msg=f"{student_proj_detail_ser.errors}")
                        return Response(
                            student_proj_detail_ser.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyProjectSerializer(uproj).data,
                    status=HTTP_202_ACCEPTED,
                )
        else:
            settings.LOGGER.error(msg=f"{base_ser.errors}")
            return Response(
                base_ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class ProjectDocs(APIView):
    permission_classes = [IsAuthenticated]

    def gos(pk):
        try:
            docs = ProjectDocument.objects.filter(project=pk).all()
        except Project.DoesNotExist:
            raise NotFound
        return docs

    def get(self, req, pk):
        # Get the docs based on the project pk
        all = self.gos(pk=pk)
        ser = MidDocumentSerializer(
            all,
            many=True,
        )
        if ser.errors:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


# PROJECTS ADDITIONAL DETAILS =============================================================================


class ProjectAdditional(APIView):
    def get(self, req):
        all = ProjectDetail.objects.all()
        ser = TinyProjectDetailSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is adding details for a project")
        ser = ProjectDetailSerializer(
            data=req.data,
        )
        if ser.is_valid():
            details = ser.save()
            return Response(
                TinyProjectDetailSerializer(details).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class ProjectAdditionalDetail(APIView):
    def go(self, pk):
        try:
            obj = ProjectDetail.objects.get(pk=pk)
        except ProjectDetail.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        details = self.go(pk)
        ser = ProjectDetailSerializer(details)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        details = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting project details")
        details.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is updating project details")
        details = self.go(pk)
        ser = ProjectDetailSerializer(
            details,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_details = ser.save()
            return Response(
                TinyProjectDetailSerializer(u_details).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class StudentProjectAdditional(APIView):
    def get(self, req):
        all = StudentProjectDetails.objects.all()
        ser = TinyStudentProjectDetailSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting student project details")
        ser = StudentProjectDetailSerializer(
            data=req.data,
        )
        if ser.is_valid():
            details = ser.save()
            return Response(
                TinyStudentProjectDetailSerializer(details).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class StudentProjectAdditionalDetail(APIView):
    def go(self, pk):
        try:
            obj = StudentProjectDetails.objects.get(pk=pk)
        except StudentProjectDetails.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        details = self.go(pk)
        ser = StudentProjectDetailSerializer(details)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        details = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting student project details {details}"
        )
        details.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        details = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating student project details: {details}"
        )
        ser = StudentProjectDetailSerializer(
            details,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_details = ser.save()
            return Response(
                TinyStudentProjectDetailSerializer(u_details).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class ExternalProjectAdditional(APIView):
    def get(self, req):
        all = ExternalProjectDetails.objects.all()
        ser = TinyExternalProjectDetailSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting external project details")
        ser = ExternalProjectDetailSerializer(
            data=req.data,
        )
        if ser.is_valid():
            details = ser.save()
            return Response(
                TinyExternalProjectDetailSerializer(details).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class ExternalProjectAdditionalDetail(APIView):
    def go(self, pk):
        try:
            obj = ExternalProjectDetails.objects.get(pk=pk)
        except ExternalProjectDetails.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        details = self.go(pk)
        ser = ExternalProjectDetailSerializer(details)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        details = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting external project details: {details}"
        )
        details.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        details = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating external project details: {details}"
        )
        ser = ExternalProjectDetailSerializer(
            details,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_details = ser.save()
            return Response(
                TinyExternalProjectDetailSerializer(u_details).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class SelectedProjectAdditionalDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Project.objects.filter(pk=pk).all()
        except Project.DoesNotExist:
            raise NotFound
        else:
            base_details = ProjectDetail.objects.filter(project=pk)
            student_details = StudentProjectDetails.objects.filter(project=pk)
            external_details = ExternalProjectDetails.objects.filter(project=pk)

            details = {
                "base_details": ProjectDetailSerializer(
                    base_details,
                    many=True,
                ).data,
                "student_details": StudentProjectDetailSerializer(
                    student_details,
                    many=True,
                ).data,
                "external_details": ExternalProjectDetailSerializer(
                    external_details,
                    many=True,
                ).data,
            }

            return details

    def get(self, req, pk):
        details = self.go(pk)
        return Response(details, status=HTTP_200_OK)


# MEMBERS =================================================================================================


class ProjectMembers(APIView):
    def get(self, req):
        try:
            page = int(req.query_params.get("page", 1))
            if page < 1:
                raise ValueError("Invalid page number.")

        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1
        page_size = getattr(settings, "PAGE_SIZE", 10)
        start = (page - 1) * page_size
        end = start + page_size

        all_members = ProjectMember.objects.all()

        # Serialize the paginated results
        ser = TinyProjectMemberSerializer(
            all_members[start:end],
            many=True,
        )
        return Response(ser.data, status=HTTP_200_OK)

    def post(self, req):
        user = req.data.get("user")
        project = req.data.get("project")
        role = req.data.get("role")
        time_allocation = req.data.get("time_allocation")
        short_code = req.data.get("short_code")
        comments = req.data.get("comments")
        is_leader = req.data.get("is_leader")
        position = req.data.get("position")
        old_id = req.data.get("old_id")

        settings.LOGGER.info(
            msg=f"{req.user} is updating project membership for {project}"
        )

        data_to_serialize = {
            "user": user,
            "project": project,
            "role": role,
            "time_allocation": time_allocation,
            "short_code": short_code,
            "comments": comments,
            "is_leader": is_leader,
            "position": position,
            "old_id": old_id,
        }

        ser = ProjectMemberSerializer(
            data=data_to_serialize,
        )
        if ser.is_valid():
            member = ser.save(is_leader=is_leader)

            return Response(
                TinyProjectMemberSerializer(member).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class PromoteToLeader(APIView):
    def go(self, user_id, project_id):
        try:
            obj = ProjectMember.objects.get(user__pk=user_id, project__pk=project_id)
        except ProjectMember.DoesNotExist:
            raise NotFound
        return obj

    def gteam(self, project_id):
        try:
            objects = ProjectMember.objects.filter(project__pk=project_id).all()
        except ProjectMember.DoesNotExist:
            raise NotFound
        return objects

    def post(self, req):
        project_id = req.data["project"]
        user_id = req.data["user"]
        user_to_become_leader_obj = self.go(user_id=user_id, project_id=project_id)
        settings.LOGGER.info(
            msg=f"{req.user} is promoting {user_to_become_leader_obj} to leader"
        )

        team = self.gteam(project_id=project_id)

        # Set is_leader to False for all members in the team
        try:

            team.update(
                is_leader=False,
            )

            # Get the IDs of team members with role "supervising" and associated users with is_staff=True
            staff_ids = team.filter(
                role="supervising", user__is_staff=True
            ).values_list("id", flat=True)
            # Get the IDs of team members with role "supervising" and associated users with is_staff=False
            non_staff_ids = team.filter(
                role="supervising", user__is_staff=False
            ).values_list("id", flat=True)

            team.filter(id__in=non_staff_ids).update(role="consulted")
            team.filter(id__in=staff_ids).update(role="research")

            # team.filter(role="supervising").update(role="research")

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")

        # Create a serializer instance with the data and set is_leader=True
        ser = ProjectMemberSerializer(
            user_to_become_leader_obj,
            data={
                "is_leader": True,
                "role": "supervising",
            },  # Include is_leader=True in the data
            partial=True,
        )
        if ser.is_valid():
            user_to_become_leader_obj = ser.save()  # Save the updated object

            return Response(
                ProjectMemberSerializer(user_to_become_leader_obj).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class ProjectLeaderDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, project_id):
        try:
            obj = ProjectMember.objects.get(project__pk=project_id, is_leader=True)
        except ProjectMember.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, project_id):
        leader = self.go(project_id)
        ser = ProjectMemberSerializer(leader)
        return Response(ser.data, status=HTTP_200_OK)


class ProjectMemberDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, user_id, project_id):
        try:
            obj = ProjectMember.objects.get(user__pk=user_id, project__pk=project_id)
        except ProjectMember.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, user_id, project_id):
        team = self.go(user_id, project_id)
        ser = ProjectMemberSerializer(team)
        return Response(ser.data, status=HTTP_200_OK)

    def delete(self, req, user_id, project_id):
        team_member = self.go(user_id, project_id)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting project member {team_member} from project id {project_id}"
        )
        team_member.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def put(self, req, user_id, project_id):
        team = self.go(user_id, project_id)
        settings.LOGGER.info(
            msg=f"{req.user} is updating project member {team} from project id {project_id}"
        )
        ser = ProjectMemberSerializer(
            team,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uteam = ser.save()
            return Response(
                TinyProjectMemberSerializer(uteam).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class MembersForProject(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectMember.objects.filter(project_id=pk).all()
        except ProjectMember.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        project_members = self.go(pk)
        ser = TinyProjectMemberSerializer(
            project_members,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is reordering members for project id {pk}"
        )
        reordered_team = req.data.get("reordered_team")

        # Create a dictionary to keep track of positions
        positions = {}
        # Assuming reordered_team is a list of dictionaries, each containing user_id and new_position
        for item in reordered_team:
            user_id = item["user"]["pk"]  # Access user_id as item["user"]["pk"]

            try:
                project_member = ProjectMember.objects.filter(
                    user_id=user_id, project_id=pk
                ).first()
            except ProjectMember.DoesNotExist as e:
                settings.LOGGER.error(msg=f"{e}")
                raise NotFound

            # Adjust the position of the member based on the new_position
            if item["is_leader"] == False and item["position"] == 1:
                item["position"] += 1

            # Check if the new position is already occupied
            new_position = item["position"]
            while new_position in positions:
                new_position += 1
            positions[new_position] = True

            # Update the project_member's position to the new_position
            project_member.position = new_position
            if item["is_leader"] == True:
                project_member.position = 1  # Set the leader's position to 1

            project_member.save()

        # Re-sort project members based on their positions
        project_members = ProjectMember.objects.filter(project_id=pk).order_by(
            "position"
        )
        ser = ProjectMemberSerializer(
            project_members,
            many=True,
        )

        return Response(
            {
                "sorted_team": ser.data,
            },
            status=HTTP_202_ACCEPTED,  # Use status from rest_framework
        )


# AREAS =================================================================================================


class ProjectAreas(APIView):
    def get(self, req):
        all = ProjectArea.objects.all()
        ser = ProjectAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a project area")
        ser = ProjectAreaSerializer(
            data=req.data,
        )
        if ser.is_valid():
            projectarea = ser.save()
            return Response(
                ProjectAreaSerializer(projectarea).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProjectAreaDetail(APIView):
    def go(self, pk):
        try:
            obj = ProjectArea.objects.get(pk=pk)
        except ProjectArea.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        projarea = self.go(pk)
        ser = ProjectAreaSerializer(projarea)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        projarea = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting project area {projarea}")
        projarea.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        projarea = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating project area {projarea}")
        ser = ProjectAreaSerializer(
            projarea,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uprojarea = ser.save()
            return Response(
                ProjectAreaSerializer(uprojarea).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AreasForProject(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectArea.objects.filter(project_id=pk).first()
        except ProjectArea.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        project_areas = self.go(pk)
        ser = ProjectAreaSerializer(
            project_areas,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req, pk):
        project_areas = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating areas for project area {project_areas}"
        )
        area_data = req.data.get("areas")
        data = {"areas": area_data}

        ser = ProjectAreaSerializer(
            project_areas,
            data=data,
            partial=True,
        )
        if ser.is_valid():
            uprojarea = ser.save()
            return Response(
                ProjectAreaSerializer(uprojarea).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# HELPER =================================================================================================
class CoreFunctionProjects(APIView):
    def get(self, req):
        all = Project.objects.filter(kind="core_function").all()
        ser = TinyProjectSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class ScienceProjects(APIView):
    def get(self, req):
        all = Project.objects.filter(kind="science").all()
        ser = TinyProjectSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class StudentProjects(APIView):
    def get(self, req):
        all = Project.objects.filter(kind="student").all()
        ser = TinyProjectSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class ExternalProjects(APIView):
    def get(self, req):
        all = Project.objects.filter(kind="external").all()
        ser = TinyProjectSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class DownloadAllProjectsAsCSV(APIView):
    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is generating a csv of projects...")
        try:
            # Retrieve projects data from the database
            projects = Project.objects.all()

            # Create a response object with CSV content type
            res = HttpResponse(content_type="text/csv")
            res["Content-Disposition"] = 'attachment; filename="projects.csv"'

            # Create a CSV writer
            writer = csv.writer(res)
            # writer.writerow(["-----", "Projects", "-----"])

            # Get field names
            # field_names = [field.name for field in Project._meta.fields]
            # id, created_at, updated_at, old_id, kind, status, year, number, title, description, tagline, keywords, start_date, end_date, business_area

            # NEEDS TO BECOME In this order
            # id, status, kind, year, title, ba, ba leader, team names (comma separated), cost_center, start_date, end_date
            # Define custom field names in the desired order
            custom_field_names = [
                "ID",
                "Status",
                "Type",
                "Year",
                "Title",
                "Business Area",
                "Business Area Leader",
                "Team Members",
                "Cost Center ID",
                "Start Date",
                "End Date",
            ]

            # 'cost_center',
            # Write CSV headers
            writer.writerow(custom_field_names)

            # Write project data rows
            for project in projects:
                row = [
                    project.pk,
                    project.status,
                    project.kind,
                    project.year,
                    project.title,
                    project.business_area,
                    (
                        project.business_area.leader if project.business_area else ""
                    ),  # Assuming business_area has a leader attribute
                    ", ".join(
                        [
                            f"{project_member.user.first_name} {project_member.user.last_name}"
                            for project_member in project.members.all()
                        ]
                    ),  # Assuming team_names is a related field with ManyToMany relationship
                    project.business_area.cost_center if project.business_area else "",
                    project.start_date,
                    project.end_date,
                ]
                writer.writerow(row)

            return res
            # Write CSV headers (CoreFunctionProject)
            # writer.writerow(field_names)

            # Write project data rows
            # for project in projects:
            #     row = [getattr(project, field) for field in field_names]
            #     writer.writerow(row)

            # return res

        # If server is down or otherwise error
        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return HttpResponse(status=500, content="Error generating CSV")
