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
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import render
from django.db import IntegrityError, transaction
from django.conf import settings
from django.utils import timezone
from math import ceil
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
import time
from django.http import HttpResponse
from documents.models import (
    ConceptPlan,
    ProgressReport,
    ProjectClosure,
    ProjectPlan,
    StudentReport,
)

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os


from documents.serializers import (
    ConceptPlanCreateSerializer,
    ConceptPlanSerializer,
    ProgressReportSerializer,
    ProjectClosureSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
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
    # MiniProjectMemberSerializer,
    StudentProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
    TinyProjectDetailSerializer,
    TinyProjectMemberSerializer,
    TinyProjectSerializer,
    TinyResearchFunctionSerializer,
    ResearchFunctionSerializer,
    TinyStudentProjectDetailSerializer,
)

from users.models import User
from .models import (
    ExternalProjectDetails,
    Project,
    ProjectDetail,
    ProjectArea,
    ProjectMember,
    ResearchFunction,
    StudentProjectDetails,
)
import csv

from datetime import datetime as dt

# from rest_framework.pagination import PageNumberPagination


# RESEARCH FUNCTIONS ==========================================================================================


class ResearchFunctions(APIView):
    def get(self, req):
        all = ResearchFunction.objects.all()
        ser = TinyResearchFunctionSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        print(req.data)
        ser = ResearchFunctionSerializer(
            data=req.data,
        )
        if ser.is_valid():
            print("valid")
            rf = ser.save()
            return Response(
                TinyResearchFunctionSerializer(rf).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ResearchFunctionDetail(APIView):
    def go(self, pk):
        try:
            obj = ResearchFunction.objects.get(pk=pk)
        except ResearchFunction.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        rf = self.go(pk)
        ser = ResearchFunctionSerializer(rf)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        rf = self.go(pk)
        rf.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        rf = self.go(pk)
        ser = ResearchFunctionSerializer(
            rf,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            urf = ser.save()
            return Response(
                TinyResearchFunctionSerializer(urf).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# PROJECTS =================================================================================================


class SmallProjectSearch(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        page = 1
        page_size = 5
        start = (page - 1) * page_size
        end = start + page_size

        search_term = req.GET.get("searchTerm")

        if req.user.is_superuser:
            projects = Project.objects.all()
        else:
            # projects = Project.objects.filter()

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
                # Get all unique years from the Project model
        unique_years = Project.objects.values_list('year', flat=True).distinct()

        # Convert the queryset to a list
        year_list = list(unique_years)

        return Response(
            year_list,
            status=HTTP_200_OK,
        )


class Projects(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]


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
        parts = search_term.split('-')
        print(len(parts))
        print(parts)
        print(parts[0].upper())

        # Check if there are at least three parts
        if len(parts) == 3:
            print('len is 3 parts')
            db_kind = self.determine_db_kind(parts[0].upper())
            kind = db_kind
            year = parts[1]
            number = parts[2]

            try:
                year_as_int = int(year)
            except Exception as e:
                print("ERROR: ", e)
                projects = Project.objects.filter(kind=kind).all()
                return projects

            print(year, len(year))
            if len(year) == 4:
                print('checking kind and year')
                projects = Project.objects.filter(kind=kind, year=year_as_int).all()
                try:
                    print("Trying to validate third part as number")
                    number_as_int = int(number)
                except Exception as e:
                    print("ERROR: ", e)
                    return projects
                else:
                    number_filter = Q(number__icontains=number_as_int)
                    projects = projects.filter(number_filter)
                    return projects
            else:
                projects = Project.objects.filter(kind=kind, year=year).all()
                return projects
            
        elif len(parts) == 2:
            print('len is 2 parts')
            year = parts[1]
            db_kind = self.determine_db_kind(parts[0].upper())
            kind = db_kind
            print(year, len(year))
            try:
                year_as_int = int(year)
            except Exception as e:
                print("ERROR: ", e)
                projects = Project.objects.filter(kind=kind).all()
                return projects
            if len(year) == 4:
                print('checking kind and year')
                projects = Project.objects.filter(kind=kind, year=year_as_int).all()
            else:
                projects = Project.objects.filter(kind=kind).all()
            return projects


    def get(self, request):
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
        ba_slug = request.GET.get("businessarea", "All")

        # Get the search term
        search_term = request.GET.get("searchTerm")
        # Handle search by project id string
        if search_term and (
            search_term.lower().startswith("cf-") or 
            search_term.lower().startswith("sp-") or 
            search_term.lower().startswith("stp-") or 
            search_term.lower().startswith("ext-")
        ):
            print("SEARCHING FOR A KEY")
            projects = self.parse_search_term(search_term=search_term)

            # if ba_slug != "All":
            #     projects = projects.filter(business_area__slug=ba_slug)

            # status_slug = request.GET.get("projectstatus", "All")
            # if status_slug != "All":
            #     projects = projects.filter(status=status_slug)

            # kind_slug = request.GET.get("projectkind", "All")
            # if kind_slug != "All":
            #     projects = projects.filter(kind=kind_slug)

            # # Interaction logic between checkboxes
            # if only_active:
            #     only_inactive = False
            # elif only_inactive:
            #     only_active = False

            # if only_active:
            #     projects = projects.filter(status__in=Project.ACTIVE_ONLY)
            # elif only_inactive:
            #     projects = projects.exclude(status__in=Project.ACTIVE_ONLY)

            # total_projects = projects.count()
            # total_pages = ceil(total_projects / page_size)

            # serialized_projects = ProjectSerializer(
            #     projects[start:end],
            #     many=True,
            #     context={
            #         "request": request,
            #         "projects": projects[start:end],
            #     },
            # )

            # response_data = {
            #     "projects": serialized_projects.data,
            #     "total_results": total_projects,
            #     "total_pages": total_pages,
            # }

            # return Response(response_data, status=HTTP_200_OK)

            # def return_slug_kind(kind):
            #     if kind == "corefunction":
            #         return "CF"
            #     elif kind == "student":
            #         return "STP"
            #     elif kind == "science":
            #         return "SP"
            #     else:
            #         return "EXT"
            # CF, SP, STP, EXT
            # year, number

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

        if ba_slug != "All":
            projects = projects.filter(business_area__slug=ba_slug)

        status_slug = request.GET.get("projectstatus", "All")
        if status_slug != "All":
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
        print(f"Image is", image)
        if isinstance(image, str):
            return image
        elif image is not None:
            print("Image is a file")
            print(image)
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
            print("File saved to:", file_path)

            return file_path

    def post(self, req):
        # DATA WRANGLING =============================================================
        # Get and print the data
        data = req.data
        print(data)

        # Extract into individual values for base information
        title = data.get("title")
        description = data.get("description")
        year = int(data.get("year"))
        creator = data.get("creator")
        kind = data.get("kind")
        image_data = req.FILES.get("imageData")
        keywords_str = data.get("keywords")

        # Convert keywords to a string and then list.
        keywords_str = keywords_str.strip("[]").replace('"', "")
        keywords_list = keywords_str.split(",")
        print(keywords_str)

        # Extract into individual values for the details
        business_area = data.get("businessArea")
        research_function = data.get("researchFunction")
        departmental_service = data.get("departmentalService")
        data_custodian = data.get("dataCustodian")
        supervising_scientist = data.get("supervisingScientist")
        dates = data.getlist("dates")

        # Convert dates to 'YYYY-MM-DD' format
        start_date_str, end_date_str = dates
        start_date = dt.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        end_date = dt.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()

        # Individual values (location)
        location_data_list = data.getlist("locations")
        status = "new"
        # DATA WRANGLING =============================================================

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
            print("LEGIT PROJECT SERIALIZER")
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
                        print(e)
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
                    print("LEGIT Area SERIALIZER")
                    try:
                        project_area_ser.save()
                    except Exception as e:
                        print(e)
                        response_data = {"error": str(e)}
                        return Response(
                            response_data,
                            HTTP_400_BAD_REQUEST,
                        )
                else:
                    print("Project Area")
                    print(project_area_ser.errors)
                    return Response(
                        project_area_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # Create an entry for project members
                project_member_data_object = {
                    "project": project_id,
                    "user": int(supervising_scientist),
                    "is_leader": True,
                    "role": "supervising" if kind == "student" else "research",
                    "old_id": 1,
                }
                print(project_member_data_object)
                project_member_ser = ProjectMemberSerializer(
                    data=project_member_data_object
                )
                if project_member_ser.is_valid():
                    # with transaction.atomic():
                    print("Legit members")
                    try:
                        project_member_ser.save()
                    except IntegrityError as e:
                        print(e)
                        print(project_member_ser.data)
                        return Response(
                            "An identical user already exists on this project",
                            HTTP_400_BAD_REQUEST,
                        )

                    except Exception as e:
                        print(e)
                        print(project_member_ser.data)
                else:
                    print("Project Members")
                    print(project_member_ser.errors)

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
                    "research_function": research_function,
                }

                print(project_detail_data_object)
                project_detail_ser = ProjectDetailSerializer(
                    data=project_detail_data_object
                )
                if project_detail_ser.is_valid():
                    # with transaction.atomic():
                    print("project details legit")
                    try:
                        print("saving details...")
                        project_detail_ser.save()
                        print("details saved")
                    except Exception as e:
                        print("Exception in save details for project")
                        print(e)
                        return Response(
                            e,
                            HTTP_400_BAD_REQUEST,
                        )
                else:
                    print("Project Detail")

                    print(project_detail_ser.errors)
                    return Response(
                        project_detail_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # Create unique entries in student table if student project
                if kind == "student":
                    print("Kind is Student")
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
                        # with transaction.atomic():
                        print("LEGIT STUDENT DETAILS SERIALIZER")
                        try:
                            student_proj_details_ser.save()
                        except Exception as e:
                            print(e)
                    else:
                        print("Student Detail")

                        print(student_proj_details_ser.errors)
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
                        print("LEGIT EXTERNAL DETAILS SERIALIZER")
                        print(external_details_data_object)
                        try:
                            external_details_ser.save()
                        except Exception as e:
                            print(e)
                    else:
                        print("External Detail")

                        print(external_details_ser.errors)
                        return Response(
                            HTTP_400_BAD_REQUEST,
                        )
                # if kind != "student" and kind != "external"
                else:
                    print(
                        f"PROJECTPK====================\n\nprojpk: {proj.pk}, project_id: {project_id}, kind: {proj.kind}\n\n===================="
                    )

                    serialized_proj = ProjectSerializer(proj)
                    print(serialized_proj.data)

                    # create document for concept plan data
                    document_serializer = ProjectDocumentCreateSerializer(
                        data={
                            "old_id": 1,
                            "kind": "concept",
                            "status": "new",
                            "project": proj.pk,
                            "creator": req.user.pk,
                            "modifier": req.user.pk,
                        }
                    )

                    if document_serializer.is_valid():
                        print("Serializer for doc is good")
                        # print(document_serializer.data)
                        # doc = document_serializer.save()
                        with transaction.atomic():
                            try:
                                print("Attempting to save doc via project view...")
                                doc = document_serializer.save()
                                print("Saved...")
                            except Exception as e:
                                print(e)
                                return Response(
                                    e,
                                    status=HTTP_400_BAD_REQUEST,
                                )
                            concept_plan_data_object = {
                                "document": doc.pk,
                                "project": proj.pk,
                                "aims": req.data.get("aims")
                                if req.data.get("aims") is not None
                                else "<p></p>",
                                "outcome": req.data.get("outcome")
                                if req.data.get("outcome") is not None
                                else "<p></p>",
                                "collaborations": req.data.get("collaborations")
                                if req.data.get("collaborations") is not None
                                else "<p></p>",
                                "strategic_context": req.data.get("strategic_context")
                                if req.data.get("strategic_context") is not None
                                else "<p></p>",
                                "staff_time_allocation": req.data.get(
                                    "staff_time_allocation"
                                )
                                if req.data.get("staff_time_allocation") is not None
                                else "<p></p>",
                                "budget": req.data.get("budget")
                                if req.data.get("budget") is not None
                                else "<p></p>",
                            }

                            concept_plan_serializer = ConceptPlanCreateSerializer(
                                data=concept_plan_data_object
                            )

                            if concept_plan_serializer.is_valid():
                                print("concept plan valid")
                                # with transaction.atomic():
                                try:
                                    concept_plan_serializer.save()
                                except Exception as e:
                                    print(f"Concept Plan error: {e}")
                                    return Response(
                                        e,
                                        status=HTTP_400_BAD_REQUEST,
                                    )
                            else:
                                print("Concept Plan ser not valid")
                                print(concept_plan_serializer.errors)
                                return Response(
                                    concept_plan_serializer.errors,
                                    status=HTTP_400_BAD_REQUEST,
                                )
                    else:
                        print("Project Document (Concept kind)")
                        print(document_serializer.errors)
                        return Response(
                            document_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyProjectSerializer(proj).data,
                    status=HTTP_201_CREATED,
                )
        else:
            print("issue in base project serializer")
            print(ser.errors)
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


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
            "student": StudentProjectDetailSerializer(
                student_details,
            ).data
            if student_details != []
            else [],
            "external": ExternalProjectDetailSerializer(
                external_details,
            ).data
            if external_details != []
            else [],
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
            "concept_plan": ConceptPlanSerializer(concept_plan).data
            if concept_plan != None
            else None,
            "project_plan": ProjectPlanSerializer(project_plan).data
            if project_plan != None
            else None,
            "progress_reports": ProgressReportSerializer(
                progress_reports, many=True
            ).data
            if progress_reports != None
            else None,
            "student_reports": StudentReportSerializer(student_reports, many=True).data
            if student_reports != None
            else None,
            "project_closure": ProjectClosureSerializer(project_closure).data
            if project_closure != None
            else None,
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
        proj = self.go(pk=pk)
        print(proj)
        ser = ProjectSerializer(proj).data
        details, documents, members, area_obj = self.get_full_object(pk)
        # print(documents)
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

    # def get(self, req, pk):
    #     proj = self.go(pk)
    #     ser = ProjectSerializer(proj)
    #     return Response(
    #         ser.data,
    #         status=HTTP_200_OK,
    #     )

    def delete(self, req, pk):
        proj = self.go(pk)
        proj.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def handle_project_image(self, image):
        print(f"Image is", image)
        if isinstance(image, str):
            return image
        elif image is not None:
            print("Image is a file")
            print(image)
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
            print("File saved to:", file_path)

            return file_path

    def put(self, req, pk):
        print(req.data)
        proj = self.go(pk)
        title = req.data.get("title")
        description = req.data.get("description")
        image = req.data.get("image")
        status = req.data.get("status")
        data_custodian = req.data.get("data_custodian")

        keywords = req.data.get("keywords")
        locations_str = req.data.get("locations")
        if locations_str:
            locations = locations_str

        dates = req.data.get("dates")
        if dates is not None:
            if isinstance(dates, list):
                start_date = dt.fromisoformat(dates[0]).date()
                end_date = dt.fromisoformat(dates[-1]).date()
            else:
                start_date = end_date = dt.fromisoformat(dates).date()
        else:
            start_date = end_date = None

        service = req.data.get("service")
        research_function = req.data.get("research_function")
        business_area = req.data.get("business_area")

        updated_base_proj_data = {
            key: value
            for key, value in {
                "title": title,
                "description": description,
                "business_area": business_area,
                "keywords": keywords,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
        }

        updated_proj_detail_data = {
            key: value
            for key, value in {
                "research_function": research_function,
                "service": service,
                "data_custodian": data_custodian,
                "modifier": req.user.pk,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
        }

        if locations_str:
            updated_proj_area_data = {
                key: value
                for key, value in {
                    "areas": json.loads(locations),
                }.items()
                if value is not None and (not isinstance(value, list) or value)
            }
        else:
            updated_proj_area_data = {}

        updated_proj_image_data = {
            key: value
            for key, value in {
                "file": image,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
        }

        print(
            # proj,
            # title,
            # description,
            # image,
            # status,
            # data_custodian,
            # keywords,
            # dates,
            # locations,
            # service,
            # research_function,
            # business_area,
            updated_base_proj_data,
            updated_proj_detail_data,
            updated_proj_area_data,
            updated_proj_image_data,
            sep="\n",
        )

        # return Response(
        #     status=HTTP_202_ACCEPTED,
        # )

        base_ser = ProjectSerializer(
            proj,
            data=updated_base_proj_data,
            partial=True,
        )

        if base_ser.is_valid():
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
                        print(detail_ser.errors)
                        return Response(
                            detail_ser.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )
                if updated_proj_image_data:
                    # Check if project already has an image:
                    try:
                        project_photo = ProjectPhoto.objects.get(project=pk)
                    except ProjectPhoto.DoesNotExist:
                        print("Could not find a related project photo")
                        # Create the object with the data
                        try:
                            image_data = {
                                "file": self.handle_project_image(image_data),
                                "uploader": req.user,
                                "project": proj,
                            }
                        except ValueError as e:
                            error_message = str(e)
                            print(error_message)
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
                            print(e)
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
                            print(img_ser.errors)
                            return Response(
                                img_ser.errors,
                                status=HTTP_400_BAD_REQUEST,
                            )
                        # project_photo.updated_at = dt.now()
                        # project_photo.save()
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
                        print(area_ser.errors)
                        return Response(
                            area_ser.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )
                return Response(
                    TinyProjectSerializer(uproj).data,
                    status=HTTP_202_ACCEPTED,
                )
        else:
            print(base_ser.errors)
            return Response(
                base_ser.errors,
                status=HTTP_400_BAD_REQUEST,
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
        details.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
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
        details.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        details = self.go(pk)
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
        details.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        details = self.go(pk)
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
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class SelectedProjectAdditionalDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = Project.objects.filter(pk=pk).all()
        except Project.DoesNotExist:
            raise NotFound
        else:
            base_details = ProjectDetail.objects.filter(project=pk)
            student_details = StudentProjectDetails.objects.filter(project=pk)
            external_details = ExternalProjectDetails.objects.filter(project=pk)

            # print(base_details)
            # print(student_details)
            # print(external_details)

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
    # pagination_class = PageNumberPagination
    # pagination_class.page_size = 100

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

        # Paginate the queryset
        # paginator = self.pagination_class()
        # paginated_members = paginator.paginate_queryset(all_members, req)

        # Serialize the paginated results
        ser = TinyProjectMemberSerializer(
            all_members[start:end],
            many=True,
        )
        # return paginator.get_paginated_response(ser.data)
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
            print("SERIALIIIIIIIIIIIIZED")
            # Set the is_leader field based on whether the user is the owner of the project
            # project_id = req.data.get("project")
            # user_id = req.data.get("user")
            # try:
            #     project = Project.objects.get(pk=project_id)
            # except Project.DoesNotExist:
            #     return Response(status=HTTP_400_BAD_REQUEST)

            # try:
            #     user = User.objects.get(pk=user_id)
            # except User.DoesNotExist:
            #     return Response(status=HTTP_400_BAD_REQUEST)

            # is_leader = user == project.owner
            member = ser.save(is_leader=is_leader)

            return Response(
                TinyProjectMemberSerializer(member).data,
                status=HTTP_201_CREATED,
            )
        else:
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
        print(req.data)
        project_id = req.data["project"]
        user_id = req.data["user"]
        user_to_become_leader_obj = self.go(user_id=user_id, project_id=project_id)

        team = self.gteam(project_id=project_id)

        # Set is_leader to False for all members in the team
        try:
            team.update(is_leader=False)
        except Exception as e:
            print(e)

        # Set is_leader to True for the user to become a leader
        # user_to_become_leader_obj.is_leader = True

        print(user_to_become_leader_obj)

        # Create a serializer instance with the data and set is_leader=True
        ser = ProjectMemberSerializer(
            user_to_become_leader_obj,
            data={"is_leader": True},  # Include is_leader=True in the data
            partial=True,
        )
        if ser.is_valid():
            user_to_become_leader_obj = ser.save()  # Save the updated object

            print("DATA", user_to_become_leader_obj)
            return Response(
                ProjectMemberSerializer(user_to_become_leader_obj).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# class PromoteToLeader(APIView):
#     # permission_classes = [IsAuthenticatedOrReadOnly]

#     def go(self, user_id, project_id):
#         try:
#             obj = ProjectMember.objects.get(user__pk=user_id, project__pk=project_id)
#         except ProjectMember.DoesNotExist:
#             raise NotFound
#         return obj

#     def gteam(self, project_id):
#         try:
#             objects = ProjectMember.objects.get(project__pk=project_id)
#         except ProjectMember.DoesNotExist:
#             raise NotFound
#         return objects

#     def post(self, req):
#         user_to_become_leader = req.GET.get("user")
#         project_id = req.GET.get("project")
#         print(user_to_become_leader)
#         user_to_become_leader_obj = self.go(
#             user_id=user_to_become_leader, project_id=project_id
#         )

#         team = self.gteam(project_id=project_id)

#         # Set is_leader to False for all members in the team
#         team.update(is_leader=False)

#         # Set is_leader to True for the user to become a leader
#         user_to_become_leader_obj.is_leader = True
#         user_to_become_leader_obj.save()

#         ser = ProjectMemberSerializer(
#             team,
#             data=req.data,
#             many=True,  # Update multiple objects
#             partial=True,
#         )
#         if ser.is_valid():
#             updated_team = ser.save()

#             # Create a serializer for the user to become a leader
#             user_to_become_leader_serializer = ProjectMemberSerializer(
#                 user_to_become_leader_obj
#             )

#             # Append the user to become a leader to the updated_team data
#             updated_team_data = ser.data + [user_to_become_leader_serializer.data]

#             return Response(
#                 updated_team_data,
#                 status=HTTP_202_ACCEPTED,
#             )
#         else:
#             return Response(
#                 ser.errors,
#                 status=HTTP_400_BAD_REQUEST,
#             )


class ProjectLeaderDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        team_member.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def put(self, req, user_id, project_id):
        team = self.go(user_id, project_id)
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
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )

    # def go(self, user_pk, project_pk):
    #     try:
    #         obj = ProjectMember.objects.get(user_pk=user_pk, project_pk=project_pk)
    #     except ProjectMember.DoesNotExist:
    #         raise NotFound
    #     return obj

    # def get(self, req, pk):
    #     team = self.go(pk)
    #     ser = ProjectMemberSerializer(team)
    #     return Response(
    #         ser.data,
    #         status=HTTP_200_OK,
    #     )

    # def delete(self, req, pk):
    #     team = self.go(pk)
    #     team.delete()
    #     return Response(
    #         status=HTTP_204_NO_CONTENT,
    #     )

    # def put(self, req, pk):
    #     team = self.go(pk)
    #     ser = ProjectMemberSerializer(
    #         team,
    #         data=req.data,
    #         partial=True,
    #     )
    #     if ser.is_valid():
    #         uteam = ser.save()
    #         return Response(
    #             TinyProjectMemberSerializer(uteam).data,
    #             status=HTTP_202_ACCEPTED,
    #         )
    #     else:
    #         return Response(
    #             ser.errors,
    #             status=HTTP_400_BAD_REQUEST,
    #         )


class MembersForProject(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        # Assuming you receive reordered_team in the request data
        reordered_team = req.data.get("reordered_team")

        # Create a dictionary to keep track of positions
        positions = {}
        # print(reordered_team)
        # Assuming reordered_team is a list of dictionaries, each containing user_id and new_position
        for item in reordered_team:
            user_id = item["user"]["pk"]  # Access user_id as item["user"]["pk"]

            try:
                project_member = ProjectMember.objects.filter(
                    user_id=user_id, project_id=pk
                ).first()
                # print(project_member[0]["user"])
                # print("\n\n\n\n")
                # print(project_member[1]["user"])
            except ProjectMember.DoesNotExist:
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

    # def put(self, req, pk):
    #     # Assuming you receive reordered_team in the request data
    #     reordered_team = req.data.get("reordered_team")

    #     # Create a dictionary to keep track of positions
    #     positions = {}
    #     print(reordered_team)
    #     # Assuming reordered_team is a list of dictionaries, each containing user_id and new_position
    #     for item in reordered_team:
    #         user_id = item["user"]["pk"]  # Access user_id as item["user"]["pk"]

    #         try:
    #             project_member = ProjectMember.objects.get(
    #                 user_id=user_id, project_id=pk
    #             )
    #         except ProjectMember.DoesNotExist:
    #             raise NotFound

    #         # Adjust the position of the member based on the new_position
    #         if item["is_leader"] == False and item["position"] == 1:
    #             item["position"] += 1
    #         elif item["is_leader"] == True:
    #             project_member.position = 1  # Set the leader's position to 1

    #         # Check if the new position is already occupied
    #         new_position = item["position"]
    #         while new_position in positions:
    #             new_position += 1
    #         positions[new_position] = True

    #         # Update the project_member's position to the new_position
    #         project_member.position = new_position
    #         project_member.save()

    #     # Re-sort project members based on their positions
    #     project_members = ProjectMember.objects.filter(project_id=pk).order_by(
    #         "position"
    #     )
    #     ser = ProjectMemberSerializer(
    #         project_members,
    #         many=True,
    #     )

    #     return Response(
    #         ser.data,
    #         status=HTTP_202_ACCEPTED,  # Use status from rest_framework
    #     )


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
            return Response(
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
        projarea.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        projarea = self.go(pk)
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
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AreasForProject(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        area_data = req.data.get('areas')
        print(f'Areas: {area_data}')
        data = {
            'areas': area_data
        }

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
            print(ser.errors)
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
        # TODO: Make it join with the other project-related tables.
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
            field_names = [field.name for field in Project._meta.fields]

            # Write CSV headers (CoreFunctionProject)
            writer.writerow(field_names)
            # print(res.data)

            # Write project data rows
            for project in projects:
                row = [getattr(project, field) for field in field_names]
                writer.writerow(row)

            return res

        # If server is down or otherwise error
        except Exception as e:
            print(e)
            return HttpResponse(status=500, content="Error generating CSV")
