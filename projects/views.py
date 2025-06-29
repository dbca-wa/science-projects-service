# region IMPORTS ====================================================================================================

import json, os, csv
from datetime import datetime as dt
from math import ceil

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q, Case, When, Value, F, IntegerField, CharField, Prefetch
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from django.db.models.functions import Cast


from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    NotFound,
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

# PROJECT SPECIFC IMPORTS -----------------------------------------------------------------------------------------

from documents.models import (
    AnnualReport,
    ConceptPlan,
    ProgressReport,
    ProjectClosure,
    ProjectDocument,
    ProjectPlan,
    StudentReport,
)


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
)
from medias.models import ProjectPhoto
from medias.serializers import TinyProjectPhotoSerializer
from users.models import User

from .serializers import (
    CreateProjectSerializer,
    ExternalProjectDetailSerializer,
    ProblematicProjectSerializer,
    ProjectAreaSerializer,
    ProjectDataTableSerializer,
    ProjectDetailSerializer,
    ProjectDetailViewSerializer,
    ProjectSerializer,
    ProjectMemberSerializer,
    ProjectUpdateSerializer,
    StudentProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
    TinyProjectDetailSerializer,
    TinyProjectMemberSerializer,
    TinyProjectSerializer,
    TinyStudentProjectDetailSerializer,
)

from .models import (
    ExternalProjectDetails,
    Project,
    ProjectDetail,
    ProjectArea,
    ProjectMember,
    StudentProjectDetails,
)

# endregion ====================================================================================================


# region PROJECTS =================================================================================================


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

        if not search_term:
            return Project.objects.none()

        # Split the search term into parts using '-'
        parts = search_term.split("-")

        # Get the project kind from the first part
        if parts and parts[0]:
            db_kind = self.determine_db_kind(parts[0].upper())
            kind = db_kind

            # If db_kind couldn't be determined, return empty queryset
            if not kind:
                return Project.objects.none()
        else:
            return Project.objects.none()

        # Initialize the base queryset with the determined kind
        projects = Project.objects.filter(kind=kind)

        # Case: prefix-year-number (e.g., "CF-2022-123")
        if len(parts) >= 3:
            # Handle year part
            if (
                parts[1] and parts[1].strip()
            ):  # Check if the year part is not empty (fix invalid literal for int)
                year = parts[1]
                try:
                    year_as_int = int(year)
                    if len(year) == 4:  # Only filter by year if it's a 4-digit year
                        projects = projects.filter(year=year_as_int)
                except (ValueError, TypeError):
                    # If year can't be converted to int, continue with just the kind filter
                    pass

            # Handle number part
            if (
                parts[2] and parts[2].strip()
            ):  # Check if the number part is not empty (fix invalid literal for int)
                number = parts[2]
                try:
                    number_as_int = int(number)
                    number_filter = Q(number__icontains=number_as_int)
                    projects = projects.filter(number_filter)
                except (ValueError, TypeError):
                    # If number can't be converted to int, continue with previous filters
                    pass

        # Case: prefix-year (e.g., "CF-2022")
        elif len(parts) == 2:
            if parts[1] and parts[1].strip():  # Check if the year part is not empty
                year = parts[1]
                try:
                    year_as_int = int(year)
                    if len(year) == 4:  # Only filter by year if it's a 4-digit year
                        projects = projects.filter(year=year_as_int)
                except (ValueError, TypeError):
                    # If year can't be converted to int, continue with just the kind filter
                    pass

        # Case: just the prefix (e.g., "CF")
        # We've already filtered by kind above, so no additional filtering needed

        # Additional N+1 Query optomisation
        projects = projects.select_related(
            "business_area",
            "business_area__division",
            "business_area__division__director",
            "business_area__division__approver",
            "business_area__leader",
            "business_area__caretaker",
            "business_area__finance_admin",
            "business_area__data_custodian",
            "business_area__image",
            "image",
            "image__uploader",
            "area",
        ).prefetch_related(
            "members",
            "members__user",
            "members__user__profile",
            "members__user__work",
            "members__user__work__business_area",
            "members__user__caretaker",
            "members__user__caretaker_for",
            "business_area__division__directorate_email_list",
            "admintasks",
        )

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

        selected_user = request.GET.get("selected_user", None)

        # # print the req data
        # print(selected_user)

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
                projects = projects.annotate(
                    number_as_text=Cast("number", output_field=CharField())
                ).filter(
                    Q(title__icontains=search_term)
                    | Q(description__icontains=search_term)
                    | Q(tagline__icontains=search_term)
                    | Q(keywords__icontains=search_term)
                    | Q(number_as_text__icontains=search_term)
                )

        if selected_user:
            projects = projects.filter(members__user__pk=selected_user)

        if ba_pk != "All":
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

        # N+1 query optimization
        projects = projects.select_related(
            "business_area",
            "business_area__division",
            "business_area__division__director",
            "business_area__division__approver",
            "business_area__leader",
            "business_area__caretaker",
            "business_area__finance_admin",
            "business_area__data_custodian",
            "business_area__image",
            "image",
            "image__uploader",
            "area",
        ).prefetch_related(
            "members",
            "members__user",
            "members__user__profile",
            "members__user__work",
            "members__user__work__business_area",
            "members__user__caretaker",
            "members__user__caretaker_for",
            "business_area__division__directorate_email_list",
            "admintasks",  # For deletion request functionality
        )

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
                                                "ae_endorsement_required": False,
                                                "ae_endorsement_provided": False,
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


class ProjectMap(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        print(f"{req.user} is viewing the map")
        settings.LOGGER.info(msg=f"{req.user} is viewing/filtering projects")
        try:
            page = int(req.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = 2000
        start = (page - 1) * page_size
        end = start + page_size

        # Get any location selections (is in json format)
        # location = req.query_params.get("locations", None)
        # print(location)
        # if location is not None:
        #     location = json.loads(location)
        #     projects = Project.objects.filter(projectarea__location__in=location).all()
        # else:
        #     projects = Project.objects.all()
        # Get the search term
        search_term = req.GET.get("searchTerm")
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
                projects = projects.annotate(
                    number_as_text=Cast("number", output_field=CharField())
                ).filter(
                    Q(title__icontains=search_term)
                    | Q(description__icontains=search_term)
                    | Q(tagline__icontains=search_term)
                    | Q(keywords__icontains=search_term)
                    | Q(number_as_text__icontains=search_term)
                )

        selected_user = req.GET.get("selected_user", None)

        if selected_user:
            projects = projects.filter(members__user__pk=selected_user)

        business_areas = req.GET.get("businessarea", None)
        if business_areas:
            business_areas = business_areas.split(",")
            projects = projects.filter(business_area__pk__in=business_areas)

        # N+1 query optimization
        projects = projects.select_related(
            "business_area",
            "business_area__division",
            "business_area__image",  # Select related for the business area image
            "image",
            "area",  # Based on serializer
        ).prefetch_related(
            "members",
        )

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

        total_projects = projects.count()
        total_pages = ceil(total_projects / page_size)

        serialized_projects = ProjectSerializer(
            projects[start:end],
            many=True,
            context={
                "request": req,
                "projects": projects[start:end],
            },
        )

        response_data = {
            "projects": serialized_projects.data,
            "total_results": total_projects,
            "total_pages": total_pages,
        }

        return Response(response_data, status=HTTP_200_OK)


class ProjectDetails(APIView):
    def go(self, pk):
        try:
            # Optimise the main project query with all related data
            obj = (
                Project.objects.select_related(
                    "business_area",
                    "business_area__division",
                    "business_area__division__director",
                    "business_area__division__approver",
                    "business_area__leader",
                    "business_area__caretaker",
                    "business_area__finance_admin",
                    "business_area__data_custodian",
                    "business_area__image",
                    "image",  # ProjectPhoto
                    "image__uploader",
                    "area",  # ProjectArea
                )
                .prefetch_related(
                    "business_area__division__directorate_email_list",
                )
                .get(pk=pk)
            )
        except Project.DoesNotExist:
            raise NotFound
        return obj

    def get_full_object(self, pk):
        try:
            obj = (
                Project.objects.select_related(
                    "business_area",
                    "business_area__division",
                    "business_area__division__director",
                    "business_area__division__approver",
                    "business_area__leader",
                    "business_area__caretaker",
                    "business_area__finance_admin",
                    "business_area__data_custodian",
                    "business_area__image",
                    "image",  # ProjectPhoto
                    "image__uploader",
                    "area",  # ProjectArea
                )
                .prefetch_related(
                    "business_area__division__directorate_email_list",
                )
                .get(pk=pk)
            )
        except Project.DoesNotExist:
            raise NotFound
        else:
            # Optimise ProjectDetail query
            base_details = ProjectDetail.objects.select_related(
                "project",
                "creator",
                "creator__profile",  # For TinyUserSerializer
                "creator__work",  # For TinyUserSerializer
                "creator__work__business_area",
                "modifier",
                "modifier__profile",
                "modifier__work",
                "modifier__work__business_area",
                "owner",
                "owner__profile",
                "owner__work",
                "owner__work__business_area",
                "data_custodian",
                "data_custodian__profile",
                "data_custodian__work",
                "data_custodian__work__business_area",
                "site_custodian",
                "site_custodian__profile",
                "site_custodian__work",
                "site_custodian__work__business_area",
                "service",
            ).get(project=obj)

        try:
            student_details = StudentProjectDetails.objects.select_related(
                "project"
            ).get(project=obj)
        except StudentProjectDetails.DoesNotExist:
            student_details = []

        try:
            external_details = ExternalProjectDetails.objects.select_related(
                "project"
            ).get(project=obj)
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
            concept_plan = (
                ConceptPlan.objects.select_related(
                    "document",
                    "document__project",
                    "document__project__business_area",
                    "document__project__business_area__division",
                    "document__project__business_area__division__director",
                    "document__project__business_area__division__approver",
                    "document__project__business_area__leader",
                    "document__project__business_area__caretaker",
                    "document__project__business_area__finance_admin",
                    "document__project__business_area__data_custodian",
                    "document__project__business_area__image",
                    "document__project__image",
                    "document__project__image__uploader",
                    "document__pdf",
                    "document__creator",
                    "document__modifier",
                )
                .prefetch_related(
                    "document__project__business_area__division__directorate_email_list",
                )
                .get(document__project=obj)
            )
        except ConceptPlan.DoesNotExist:
            concept_plan = None

        try:
            project_plan = (
                ProjectPlan.objects.select_related(
                    "document",
                    "document__project",
                    "document__project__business_area",
                    "document__project__business_area__division",
                    "document__project__business_area__division__director",
                    "document__project__business_area__division__approver",
                    "document__project__business_area__leader",
                    "document__project__business_area__caretaker",
                    "document__project__business_area__finance_admin",
                    "document__project__business_area__data_custodian",
                    "document__project__business_area__image",
                    "document__project__image",
                    "document__project__image__uploader",
                    "document__pdf",
                    "document__creator",
                    "document__modifier",
                )
                .prefetch_related(
                    "document__project__business_area__division__directorate_email_list",
                )
                .get(document__project=obj)
            )
        except ProjectPlan.DoesNotExist:
            project_plan = None

        try:
            progress_reports = (
                ProgressReport.objects.select_related(
                    "document",
                    "document__project",
                    "document__project__business_area",
                    "document__project__business_area__division",
                    "document__project__business_area__division__director",
                    "document__project__business_area__division__approver",
                    "document__project__business_area__leader",
                    "document__project__business_area__caretaker",
                    "document__project__business_area__finance_admin",
                    "document__project__business_area__data_custodian",
                    "document__project__business_area__image",
                    "document__project__image",
                    "document__project__image__uploader",
                    "document__pdf",
                    "document__creator",
                    "document__modifier",
                    "report",  # TinyAnnualReportSerializer
                )
                .prefetch_related(
                    "document__project__business_area__division__directorate_email_list",
                )
                .filter(document__project=obj)
                .all()
            )
        except ProgressReport.DoesNotExist:
            progress_reports = None

        try:
            student_reports = (
                StudentReport.objects.select_related(
                    "document",
                    "document__project",
                    "document__project__business_area",
                    "document__project__business_area__division",
                    "document__project__business_area__division__director",
                    "document__project__business_area__division__approver",
                    "document__project__business_area__leader",
                    "document__project__business_area__caretaker",
                    "document__project__business_area__finance_admin",
                    "document__project__business_area__data_custodian",
                    "document__project__business_area__image",
                    "document__project__image",
                    "document__project__image__uploader",
                    "document__pdf",
                    "document__creator",
                    "document__modifier",
                    "report",  # AnnualReport
                    "report__creator",
                    "report__modifier",
                )
                .prefetch_related(
                    "document__project__business_area__division__directorate_email_list",
                )
                .filter(document__project=obj)
                .all()
            )
        except StudentReport.DoesNotExist:
            student_reports = None

        try:
            project_closure = (
                ProjectClosure.objects.select_related(
                    "document",
                    "document__project",
                    "document__project__business_area",
                    "document__project__business_area__division",
                    "document__project__business_area__division__director",
                    "document__project__business_area__division__approver",
                    "document__project__business_area__leader",
                    "document__project__business_area__caretaker",
                    "document__project__business_area__finance_admin",
                    "document__project__business_area__data_custodian",
                    "document__project__business_area__image",
                    "document__project__image",
                    "document__project__image__uploader",
                    "document__pdf",
                    "document__creator",
                    "document__modifier",
                )
                .prefetch_related(
                    "document__project__business_area__division__directorate_email_list",
                )
                .get(document__project=obj)
            )
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
            # CRITICAL: Optimize project members query
            project_members = (
                ProjectMember.objects.select_related(
                    "user",
                    "user__profile",
                    "user__work",
                    "user__work__business_area",
                    "user__work__business_area__division",
                    "user__work__business_area__division__director",
                    "user__work__business_area__division__approver",
                    "user__work__business_area__leader",
                    "user__work__business_area__caretaker",
                    "user__work__business_area__finance_admin",
                    "user__work__business_area__data_custodian",
                    "user__work__business_area__image",
                    "project",
                    "project__business_area",
                    "project__business_area__division",
                    "project__business_area__image",
                    "project__image",
                )
                .prefetch_related(
                    "user__work__business_area__division__directorate_email_list",
                    "project__business_area__division__directorate_email_list",
                )
                .filter(project=obj)
            )
        except ProjectMember.DoesNotExist:
            project_members = None

        members = (
            TinyProjectMemberSerializer(project_members, many=True).data
            if project_members != None
            else None
        )

        try:
            project_areas = ProjectArea.objects.select_related("project").get(
                project=obj
            )
        except ProjectArea.DoesNotExist:
            project_areas = None

        area_obj = (
            ProjectAreaSerializer(project_areas).data if project_areas != None else None
        )

        return details, documents, members, area_obj

    def get(self, req, pk):
        proj = self.go(pk=pk)
        settings.LOGGER.info(msg=f"{req.user} is viewing project: {proj}")
        ser = ProjectSerializer(proj).data
        details, documents, members, area_obj = self.get_full_object(pk)

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
        business_area = req.data.get("businessArea")

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

        # print(updated_base_proj_data)

        updated_proj_detail_data = {
            key: value
            for key, value in {
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
            if value is not None and (not isinstance(value, list) or value)
        }

        updated_external_project_data = {
            key: value
            for key, value in {
                "description": external_description,
                "aims": aims,
                "budget": budget,
                "collaboration_with": collaboration_with,
            }.items()
            if value is not None and (not isinstance(value, list) or value)
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
            with transaction.atomic():
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
                    else:
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


class ToggleUserProfileVisibilityForProject(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        proj = self.go(pk)
        print(req.data)
        userPk = req.data.get("user_pk")
        settings.LOGGER.info(
            msg=f"{req.user} is toggling ({userPk}) user profile visibility for project: {proj}"
        )
        try:
            # Access the array hidden_from_staff_profiles and if the user's pk is in it, remove it, otherwise add it
            if userPk in proj.hidden_from_staff_profiles:
                proj.hidden_from_staff_profiles.remove(userPk)
            else:
                proj.hidden_from_staff_profiles.append(userPk)
            proj.save()
            return Response(
                TinyProjectSerializer(proj).data,
                status=HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return Response({"error": f"{e}"}, status=HTTP_400_BAD_REQUEST)


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
            project_ids = ProjectMember.objects.filter(user=req.user).values_list(
                "project__id", flat=True
            )
            projects = Project.objects.filter(id__in=project_ids).order_by("title")

        if search_term:
            projects = projects.filter(title__icontains=search_term)

        # Optimise based on TinyProjectSerializer needs
        projects = projects.select_related("business_area", "image")

        serialized_projects = TinyProjectSerializer(
            projects[start:end], many=True, context={"request": req}
        ).data

        response_data = {"projects": serialized_projects}
        return Response(response_data, status=HTTP_200_OK)


class MyProjects(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        if not req.user.is_authenticated:
            return Response(
                {"detail": "You are not logged in."}, status=HTTP_401_UNAUTHORIZED
            )

        # Get project memberships with optimized select_related to prevent N+1
        user_memberships = (
            ProjectMember.objects.filter(user=req.user)
            .select_related(
                "project",
                "project__business_area",
                "project__business_area__division",  # For TinyDivisionSerializer
                "project__business_area__image",  # OneToOne
                "project__image",  # Project image
                "project__image__uploader",  # Project image uploader (if needed)
            )
            .prefetch_related(
                # "project__business_area__division__directorate_email_list"
                Prefetch(
                    "project__business_area__division__directorate_email_list",
                    queryset=User.objects.only(
                        "pk", "email", "display_first_name", "display_last_name"
                    ),
                )
            )
        )

        projects_with_roles = [
            (membership.project, membership.role) for membership in user_memberships
        ]
        projects = [proj for proj, _ in projects_with_roles]

        serialized_projects = ProjectDataTableSerializer(
            projects,
            many=True,
            context={"projects_with_roles": projects_with_roles},
        )

        return Response(
            serialized_projects.data,
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


# endregion =============================================================================================

# region Project Docs =============================================================================================


class ProjectDocs(APIView):
    permission_classes = [IsAuthenticated]

    def gos(pk):
        try:
            docs = ProjectDocument.objects.filter(project=pk).all()
        except Project.DoesNotExist:
            raise NotFound
        return docs

    def get(self, req, pk):
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


# endregion =============================================================================================


# region PROJECTS ADDITIONAL DETAILS =============================================================================


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


# endregion =============================================================================================


# region MEMBERS =================================================================================================


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

        # Check if any other members exist,
        # if they dont set is_leader to true.
        # If exists, but none of them have is_leader, set it to true
        existing_members = ProjectMember.objects.filter(project=project)
        if not existing_members.exists():
            is_leader = True
            role = "supervising"
        elif not existing_members.filter(is_leader=True).exists():
            is_leader = True
            role = "supervising"

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
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to promote a user to leader"
        )
        project_id = req.data["project"]
        user_id = req.data["user"]
        if not project_id or not user_id:
            settings.LOGGER.error(msg=f"Project ID and User ID are required")
            return Response(
                {"detail": "Project ID and User ID are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        user_to_become_leader_obj = self.go(user_id=user_id, project_id=project_id)
        settings.LOGGER.info(
            msg=f"{req.user} is promoting {user_to_become_leader_obj} to leader"
        )

        team = self.gteam(project_id=project_id)

        # Set is_leader to False for all members in the team
        try:
            # Update leaders/set pos to +1 of its prev num
            team.update(is_leader=False, position=F("position") + 1)

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
                "position": 1,
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


# endregion =================================================================================================


# region Problematic Projects =============================================================================================


class UnapprovedThisFY(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is Getting Unapproved Projects for latest FY"
        )

        # Get the latest report year efficiently
        latest_report = AnnualReport.objects.only("year").order_by("-year").first()

        if not latest_report:
            return Response({"error": "No annual reports found"}, status=404)

        latest_year = latest_report.year

        # Get all unapproved documents for the latest year with optimized prefetching
        unapproved_documents = (
            ProjectDocument.objects.filter(
                # Include documents that belong to progress/student reports of the latest year
                # OR documents created in the latest year (for concept plans, project plans, closures)
                Q(progress_report_details__year=latest_year)
                | Q(student_report_details__year=latest_year)
                | Q(created_at__year=latest_year)
            )
            .filter(
                # Filter for documents that don't have all three approvals
                Q(project_lead_approval_granted=False)
                | Q(business_area_lead_approval_granted=False)
                | Q(directorate_approval_granted=False)
            )
            .select_related(
                "project__business_area",  # Business area details
                "creator",  # Document creator
                "modifier",  # Document modifier
            )
            .prefetch_related(
                # Prefetch project members to get project leader
                Prefetch(
                    "project__members",
                    queryset=ProjectMember.objects.filter(
                        is_leader=True
                    ).select_related("user"),
                    to_attr="project_leaders",
                ),
                # Prefetch business area leader
                "project__business_area__leader",
                # Prefetch the specific report details
                "progress_report_details",
                "student_report_details",
                "concept_plan_details",
                "project_plan_details",
                "project_closure_details",
            )
            .distinct()
        )

        # Structure the response by document kind
        response_data = {
            "latest_year": latest_year,
            "concept": [],
            "project_plan": [],
            "progress_report": [],
            "student_report": [],
            "project_closure": [],
            "all": [],
        }

        for doc in unapproved_documents:
            # Get project leader email
            project_leader_email = None
            if hasattr(doc.project, "project_leaders") and doc.project.project_leaders:
                project_leader_email = doc.project.project_leaders[0].user.email

            # Get business area leader email and name
            business_area_leader_email = None
            business_area_name = None
            if doc.project.business_area:
                business_area_name = doc.project.business_area.name
                if doc.project.business_area.leader:
                    business_area_leader_email = doc.project.business_area.leader.email

            # Create the base document data
            doc_data = {
                "project_id": doc.project.id,
                "document_id": doc.id,
                "kind": doc.kind,
                "project_title": doc.project.title,
                "project_leader_email": project_leader_email,
                "business_area_leader_email": business_area_leader_email,
                "business_area_name": business_area_name,
                "project_lead_approval_granted": doc.project_lead_approval_granted,
                "business_area_lead_approval_granted": doc.business_area_lead_approval_granted,
                "directorate_approval_granted": doc.directorate_approval_granted,
                "status": doc.status,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
            }

            # Add to appropriate category and to 'all'
            if doc.kind == ProjectDocument.CategoryKindChoices.CONCEPTPLAN:
                response_data["concept"].append(doc_data)
            elif doc.kind == ProjectDocument.CategoryKindChoices.PROJECTPLAN:
                response_data["project_plan"].append(doc_data)
            elif doc.kind == ProjectDocument.CategoryKindChoices.PROGRESSREPORT:
                response_data["progress_report"].append(doc_data)
            elif doc.kind == ProjectDocument.CategoryKindChoices.STUDENTREPORT:
                response_data["student_report"].append(doc_data)
            elif doc.kind == ProjectDocument.CategoryKindChoices.PROJECTCLOSURE:
                response_data["project_closure"].append(doc_data)

            # Add to 'all' regardless of kind
            response_data["all"].append(doc_data)

        return Response(response_data)


class ProblematicProjects(APIView):
    permission_classes = [IsAuthenticated]

    def get_projects(self):
        try:
            # Optimise for the ProblematicProjectSerializer needs
            # Added prefetch for documents to avoid N+1 queries when checking for closure documents
            projects = (
                Project.objects.all()
                .select_related("business_area", "image")
                .prefetch_related("members", "members__user", "documents")
            )
        except Project.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
        return projects

    def get(self, req):
        try:
            settings.LOGGER.info(msg=f"{req.user} is Getting All Problematic Projects")

            all_projects = self.get_projects()
            memberless_projects = []
            no_leader_tag_projects = []
            multiple_leader_tag_projects = []
            externally_led_projects = []
            open_closed_projects = []

            for p in all_projects:
                members = p.members.all()  # No DB hit thanks to prefetch_related
                leader_tag_count = 0
                external_leader = False

                # Check if project has fully approved closure document but is not in closed state
                has_approved_closure_document = p.documents.filter(
                    kind=ProjectDocument.CategoryKindChoices.PROJECTCLOSURE,
                    directorate_approval_granted=True,
                ).exists()

                is_closed = p.status in Project.CLOSED_ONLY

                if has_approved_closure_document and not is_closed:
                    open_closed_projects.append(p)

                for mem in members:
                    if mem.role == ProjectMember.RoleChoices.SUPERVISING:
                        leader_tag_count += 1
                    if mem.is_leader == True and mem.user.is_staff == False:
                        external_leader = True

                if len(members) < 1:
                    memberless_projects.append(p)
                else:
                    if external_leader:
                        externally_led_projects.append(p)
                    if leader_tag_count == 0:
                        no_leader_tag_projects.append(p)
                    elif leader_tag_count > 1:
                        multiple_leader_tag_projects.append(p)

            data = {
                "open_closed": ProblematicProjectSerializer(
                    open_closed_projects,
                    many=True,
                ).data,
                "no_members": ProblematicProjectSerializer(
                    memberless_projects, many=True
                ).data,
                "no_leader": ProblematicProjectSerializer(
                    no_leader_tag_projects, many=True
                ).data,
                "external_leader": ProblematicProjectSerializer(
                    externally_led_projects, many=True
                ).data,
                "multiple_leads": ProblematicProjectSerializer(
                    multiple_leader_tag_projects, many=True
                ).data,
            }

            return Response(data=data, status=HTTP_200_OK)

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"msg": str(e)}, HTTP_400_BAD_REQUEST)


# Where the project is open but it has an approved closure
class RemedyOpenClosed(APIView):
    permission_classes = [IsAuthenticated]

    # Get the project itself
    def get_project(self, project_pk):
        try:
            project = Project.objects.get(pk=project_pk)
        except Project.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            return None
        return project

    def post(self, req):
        try:
            # get the array of pks
            open_closed_projects = req.data.get("projects", [])
            settings.LOGGER.warning(
                msg=f"{req.user} is remedying open closed projects\nArray: {open_closed_projects}"
            )

            if not open_closed_projects:
                return Response(
                    {"error": "No projects provided"}, status=HTTP_400_BAD_REQUEST
                )

            # Bulk fetch all projects to avoid N+1 queries
            projects = Project.objects.filter(pk__in=open_closed_projects).only(
                "pk", "title"
            )
            projects_dict = {p.pk: p for p in projects}

            # Find all approved closure documents for these projects in one query
            approved_closure_docs = (
                ProjectDocument.objects.filter(
                    project_id__in=open_closed_projects,
                    kind=ProjectDocument.CategoryKindChoices.PROJECTCLOSURE,
                    directorate_approval_granted=True,
                )
                .select_related("project")
                .only("pk", "project_id", "project__title")
            )

            # Group closure documents by project
            closure_docs_by_project = {}
            for doc in approved_closure_docs:
                project_id = doc.project_id
                if project_id not in closure_docs_by_project:
                    closure_docs_by_project[project_id] = []
                closure_docs_by_project[project_id].append(doc)

            remedied_projects = []
            failed_projects = []

            # Process each requested project
            for proj_pk in open_closed_projects:
                try:
                    # Check if project exists
                    if proj_pk not in projects_dict:
                        failed_projects.append(
                            {"project_id": proj_pk, "error": "Project not found"}
                        )
                        continue

                    project = projects_dict[proj_pk]

                    # Check if project has approved closure documents
                    if proj_pk in closure_docs_by_project:
                        closure_docs = closure_docs_by_project[proj_pk]
                        deleted_count = len(closure_docs)

                        # Delete the closure documents (bulk delete for efficiency)
                        doc_ids = [doc.pk for doc in closure_docs]
                        ProjectDocument.objects.filter(pk__in=doc_ids).delete()

                        remedied_projects.append(
                            {
                                "project_id": proj_pk,
                                "project_title": project.title,
                                "deleted_closure_docs": deleted_count,
                            }
                        )

                        if project.status == Project.StatusChoices.SUSPENDED:
                            project.status = Project.StatusChoices.ACTIVE
                            project.save()

                        settings.LOGGER.info(
                            msg=f"Remedied project {proj_pk}: deleted {deleted_count} approved closure document(s)"
                        )
                    else:
                        failed_projects.append(
                            {
                                "project_id": proj_pk,
                                "error": "No approved closure documents found",
                            }
                        )

                except Exception as e:
                    failed_projects.append({"project_id": proj_pk, "error": str(e)})
                    settings.LOGGER.error(
                        msg=f"Failed to remedy project {proj_pk}: {e}"
                    )

            response_data = {
                "remedied_projects": remedied_projects,
                "failed_projects": failed_projects,
                "total_processed": len(open_closed_projects),
                "successful": len(remedied_projects),
                "failed": len(failed_projects),
            }

            return Response(
                data=response_data,
                status=HTTP_200_OK,
            )

        except Exception as e:
            settings.LOGGER.error(msg=f"RemedyOpenClosed error: {e}")
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


# Where the project has 0 members
class RemedyMemberlessProjects(APIView):

    permission_classes = [IsAuthenticated]

    # Get the project itself
    def get_project(self, project_pk):
        try:
            project = Project.objects.get(pk=project_pk)
        except Project.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            return None
        return project

    # Check to see if the project has any documents, return the first one if it does
    # (concept, project, progress/student rep, closure)
    def get_first_document_if_exists(self, project_pk):
        documents_list = ProjectDocument.objects.filter(project=project_pk)
        concept_plan = None
        project_plan = None
        progress_report = None
        student_report = None
        closure = None

        progress_reports = []
        student_reports = []
        for doc in documents_list:
            if doc.kind == "concept":
                concept_plan = doc
            elif doc.kind == "project":
                project_plan = doc
            elif doc.kind == "progress_report":
                progress_reports.append(doc)
            elif doc.kind == "student_report":
                student_reports.append(doc)
            else:
                closure = doc

        if len(progress_reports) >= 1:
            progress_reports = sorted(progress_reports, key=lambda x: x.created_at)
            progress_report = progress_reports[0]

        if len(student_reports) >= 1:
            student_reports = sorted(student_reports, key=lambda x: x.created_at)
            student_report = student_reports[0]

        if concept_plan is not None:
            return concept_plan
        elif project_plan is not None:
            return project_plan
        elif progress_report is not None:
            return progress_report
        elif student_report is not None:
            return student_report
        elif closure is not None:
            return closure
        else:
            return None

    def post(self, req):
        try:
            # get the array of pks
            memberless_projects_pk_array = req.data.get("projects")
            settings.LOGGER.warning(
                msg=f"{req.user} is remedying memberless projects\nArray: {memberless_projects_pk_array}"
            )
            for proj in memberless_projects_pk_array:
                # check to see if the project has any documents.
                first_doc = self.get_first_document_if_exists(project_pk=proj)
                # If it does, add the creator of the first document  and set them as the leader
                if first_doc is not None:
                    creator = first_doc.creator
                    print(creator)
                    project = self.get_project(project_pk=proj)
                    new_leader_member = ProjectMember.objects.create(
                        project=project,
                        user=creator,
                        is_leader=True,
                        role=ProjectMember.RoleChoices.SUPERVISING,
                        time_allocation=1,
                        position=1,
                        short_code="",
                        comments="Added to memberless project",
                        old_id=0,
                    )
                # If it doesn't have either, do nothing
            return Response(
                status=HTTP_200_OK,
            )
        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"e": e}, status=HTTP_400_BAD_REQUEST)


# Where there are users but no one has leader tag
class RemedyNoLeaderProjects(APIView):
    def get_members(self, project_pk):
        try:
            members = ProjectMember.objects.filter(project=project_pk)
        except ProjectMember.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            return None
        return members

    def post(self, req):
        try:
            # get the array of pks
            leaderless_projects_pk_array = req.data.get("projects")
            settings.LOGGER.warning(
                msg=f"{req.user} is remedying leaderless projects\nArray: {leaderless_projects_pk_array}"
            )
            for proj in leaderless_projects_pk_array:
                members = self.get_members(project_pk=proj)
                # Adjust position of members
                for mem in members:
                    if mem.is_leader == False:
                        mem.position += 1
                    else:
                        # Update the leader role and move them to position 1
                        mem.role = "supervising"
                        mem.position = 1
                    mem.save()
            return Response(
                HTTP_200_OK,
            )

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"e": e}, status=HTTP_400_BAD_REQUEST)


# Where there are multiple users with the leader tag
class RemedyMultipleLeaderProjects(APIView):
    def get_members(self, project_pk):
        try:
            members = ProjectMember.objects.filter(project=project_pk)
        except ProjectMember.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            return None
        return members

    def post(self, req):
        try:
            # get the array of pks
            multiple_leader_projects_pk_array = req.data.get("projects")
            settings.LOGGER.warning(
                msg=f"{req.user} is remedying multiple lead projects\nArray: {multiple_leader_projects_pk_array}"
            )
            for proj in multiple_leader_projects_pk_array:
                members = self.get_members(project_pk=proj)
                lead_roles = members.filter(role="supervising")
                # Adjust position of members
                for mem in lead_roles:
                    if mem.is_leader == False:
                        mem.position += 1
                        if mem.project.kind is not Project.CategoryKindChoices.STUDENT:
                            if mem.user.is_staff == False:
                                mem.role = ProjectMember.RoleChoices.CONSULTED
                            else:
                                mem.role = ProjectMember.RoleChoices.RESEARCH
                        else:
                            if mem.user.is_staff == False:
                                if members.filter(
                                    role=ProjectMember.RoleChoices.STUDENT
                                ).exists():
                                    mem.role = ProjectMember.RoleChoices.ACADEMICSUPER
                                else:
                                    mem.role = ProjectMember.RoleChoices.STUDENT
                            else:
                                mem.role = ProjectMember.RoleChoices.RESEARCH
                    else:
                        if mem.user.is_staff:
                            mem.role = ProjectMember.RoleChoices.SUPERVISING
                            mem.position = 1
                        # Do nothing for externals

                    mem.save()

                # Ensure that the leader has the role/post in case they didnt have the project lead role
                for user in members:
                    if user.is_leader and user.user.is_staff:
                        user.role = ProjectMember.RoleChoices.SUPERVISING
                        user.position = 1
                        user.save()

            return Response(
                HTTP_200_OK,
            )

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"e": e}, status=HTTP_400_BAD_REQUEST)


# Where an external leader is set with the is_leader tag
class RemedyExternalLeaderProjects(APIView):
    def get_members(self, project_pk):
        try:
            members = ProjectMember.objects.filter(project=project_pk)
        except ProjectMember.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            return None
        return members

    # Check to see if the project has any documents, return the first one if it does
    # (concept, project, progress/student rep, closure)
    def get_first_document_if_exists(self, project_pk):
        documents_list = ProjectDocument.objects.filter(project=project_pk)
        concept_plan = None
        project_plan = None
        progress_report = None
        student_report = None
        closure = None

        progress_reports = []
        student_reports = []
        for doc in documents_list:
            if doc.kind == "concept":
                concept_plan = doc
            elif doc.kind == "project":
                project_plan = doc
            elif doc.kind == "progress_report":
                progress_reports.append(doc)
            elif doc.kind == "student_report":
                student_reports.append(doc)
            else:
                closure = doc

        if len(progress_reports) >= 1:
            progress_reports = sorted(progress_reports, key=lambda x: x.created_at)
            progress_report = progress_reports[0]

        if len(student_reports) >= 1:
            student_reports = sorted(student_reports, key=lambda x: x.created_at)
            student_report = student_reports[0]

        if concept_plan is not None:
            return concept_plan
        elif project_plan is not None:
            return project_plan
        elif progress_report is not None:
            return progress_report
        elif student_report is not None:
            return student_report
        elif closure is not None:
            return closure
        else:
            return None

    def post(self, req):
        try:
            # get the array of pks
            externally_led_project_pk_array = req.data.get("projects")
            settings.LOGGER.warning(
                msg=f"{req.user} is remedying externally led projects\nArray: {externally_led_project_pk_array}"
            )
            # Perform similar logic to memberless projects - searching creators of documents and setting them as leader if they are in the team
            for proj in externally_led_project_pk_array:
                # Get members list
                members = self.get_members(project_pk=proj)
                # skup if no members
                if not members:
                    continue

                # Extract users from the membership list
                users_in_membership = [membership.user for membership in members]
                # Check if a doc exists
                first_doc = self.get_first_document_if_exists(project_pk=proj)
                # If it does, add the creator of the first document and set them as the leader if they are on the team
                if first_doc is not None:
                    creator = first_doc.creator
                    print(creator)
                    # set the creator to the leader if they are staff and in the team
                    if creator.is_staff and creator in users_in_membership:
                        # set any external leaders membership to is_leader = False
                        for mem in members:
                            if mem.user.is_staff == False:
                                mem.is_leader = False
                                mem.position += 1
                            if mem.user == creator:
                                mem.role == ProjectMember.RoleChoices.SUPERVISING
                                mem.position = 1
                                mem.is_leader = True
                            mem.save()
                # If no docs, check members to set the leader to the highest level staff member
                else:
                    leader = members.filter(
                        is_leader=True, user__is_staff=False
                    ).first()
                    staff_non_leaders = members.filter(
                        is_leader=False, user__is_staff=True
                    )
                    staff_exists = staff_non_leaders.exists()

                    if staff_exists and leader:
                        leader.is_leader = False
                        leader.position += 1
                        leader.save()

                        # If there is only one staff, set them as the leader
                        if len(staff_non_leaders) == 1:
                            the_staff_membership = staff_non_leaders.first()
                            the_staff_membership.is_leader = True
                            the_staff_membership.role = (
                                ProjectMember.RoleChoices.SUPERVISING
                            )
                            the_staff_membership.position = 1
                            the_staff_membership.save()
                        # If there are multiple, set the one that was created first as leader
                        else:
                            # order by created first
                            sorted_staff = staff_non_leaders.order_by("created_at")

                            # grab the first one
                            the_staff_membership = sorted_staff.first()
                            # set the stats and save
                            the_staff_membership.is_leader = True
                            the_staff_membership.role = (
                                ProjectMember.RoleChoices.SUPERVISING
                            )
                            the_staff_membership.position = 1
                            the_staff_membership.save()

            return Response(
                HTTP_200_OK,
            )

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"e": e}, status=HTTP_400_BAD_REQUEST)


# endregion =============================================================================================


# region Project AREAS =================================================================================================


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


# endregion =================================================================================================


# region HELPER =================================================================================================


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

        # If server is down or otherwise error
        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return HttpResponse(status=500, content="Error generating CSV")


# endregion =================================================================================================
