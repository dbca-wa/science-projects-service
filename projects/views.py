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
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import render
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from math import ceil
from django.db.models import Q
from django.shortcuts import get_object_or_404

import time
from django.http import HttpResponse
from documents.models import (
    ConceptPlan,
    ProgressReport,
    ProjectClosure,
    ProjectPlan,
    StudentReport,
)

from documents.serializers import (
    ConceptPlanSerializer,
    ProgressReportSerializer,
    ProjectClosureSerializer,
    ProjectPlanSerializer,
    StudentReportSerializer,
    TinyConceptPlanSerializer,
    TinyProgressReportSerializer,
    TinyProjectClosureSerializer,
    TinyProjectPlanSerializer,
    TinyStudentReportSerializer,
)

from .serializers import (
    ExternalProjectDetailSerializer,
    ProjectAreaSerializer,
    ProjectDetailSerializer,
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
        ser = ResearchFunctionSerializer(
            data=req.data,
        )
        if ser.is_valid():
            rf = ser.save()
            return Response(
                TinyResearchFunctionSerializer(rf).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
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


class Projects(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = 12
        start = (page - 1) * page_size
        end = start + page_size

        search_term = request.GET.get("searchTerm")

        # Get the values of the checkboxes
        only_active = bool(request.GET.get("only_active", False))
        only_inactive = bool(request.GET.get("only_inactive", False))

        ba_slug = request.GET.get("businessarea", "All")
        projects = Project.objects.all()

        if ba_slug != "All":
            projects = projects.filter(business_area__slug=ba_slug)

        status_slug = request.GET.get("projectstatus", "All")
        if status_slug != "All":
            projects = projects.filter(status=status_slug)

        kind_slug = request.GET.get("projectkind", "All")
        if kind_slug != "All":
            projects = projects.filter(kind=kind_slug)

        # Interaction logic between checkboxes
        if only_active:
            only_inactive = False
        elif only_inactive:
            only_active = False

        if search_term:
            projects = projects.filter(
                Q(title__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(tagline__icontains=search_term)
                | Q(keywords__icontains=search_term)
            )

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

    def post(self, req):
        # Get the data out of the request =========
        data = req.data
        # Individual values (base)

        year = int(data.get("year"))  # Extract the integer value from the list
        creator = data.get("creator")
        kind = data.get("kind")
        title = data.get("title")
        description = data.get("description")
        print(data)

        keywords_str = data.get("keywords")
        keywords_str = keywords_str.strip("[]").replace('"', "")
        keywords_list = keywords_str.split(",")

        print(keywords_str)
        # # Convert list of keywords to a single string
        # keywords_str = ", ".join(keywords)  # Use comma and space as separator

        image_data = req.FILES.get("imageData")

        # Individual values (details)
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

        # Create the base project to send for creation ===============
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

        ser = ProjectSerializer(data=project_data_object)
        if ser.is_valid():
            with transaction.atomic():
                print("LEGIT PROJECT SERIALIZER")
                proj = ser.save()
                project_id = proj.pk
                print(project_id)

                # Create an entry for project areas
                project_area_data_object = {
                    "project": project_id,
                    "areas": location_data_list,
                }
                print(project_area_data_object)

                project_area_ser = ProjectAreaSerializer(data=project_area_data_object)
                if project_area_ser.is_valid():
                    print("LEGIT Area SERIALIZER")
                    try:
                        project_area_ser.save()
                    except Exception as e:
                        print(e)
                else:
                    print("Project Area")
                    print(project_area_ser.errors)
                    return Response(
                        project_area_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                print("here")
                # Create an entry for project members
                project_member_data_object = {
                    "project": project_id,
                    "user": supervising_scientist,
                    "is_leader": True,
                    "role": "supervising",
                    "old_id": 1,
                }
                print(project_member_data_object)
                project_member_ser = ProjectMemberSerializer(
                    data=project_member_data_object
                )
                if project_member_ser.is_valid():
                    print("Legit members")
                    try:
                        project_member_ser.save()
                    except Exception as e:
                        print(e)
                else:
                    print("Project Members")
                    print(project_member_ser.errors)

                    return Response(
                        project_member_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # Create an entry for project details
                project_detail_data_object = {
                    "project": project_id,
                    "creator": creator,
                    "modifier": creator,
                    "owner": creator,
                    "data_custodian": data_custodian,
                    # site_custodian:,
                    "research_function": research_function,
                }

                print(project_detail_data_object)
                project_detail_ser = ProjectDetailSerializer(
                    data=project_detail_data_object
                )
                if project_detail_ser.is_valid():
                    print("project details legit")
                    try:
                        project_detail_ser.save()
                    except Exception as e:
                        print(e)
                else:
                    print("Project Detail")

                    print(project_detail_ser.errors)
                    return Response(
                        project_detail_ser.errors,
                        HTTP_400_BAD_REQUEST,
                    )

                # Create unique entries in student table if student project
                if kind == "student":
                    level = data.get("level")[0]
                    organisation = data.get("organisation")[0]
                    old_id = 1

                    # Create the object
                    student_project_details_data_object = {
                        "project": project_id,
                        "organisation": organisation,
                        "level": level,
                    }

                    student_proj_details_ser = StudentProjectDetailSerializer(
                        data=student_project_details_data_object
                    )
                    if student_proj_details_ser.is_valid():
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
                if kind == "external":
                    old_id = 1
                    externalDescription = data.get("externalDescription")[0]
                    aims = data.get("aims")[0]
                    budget = data.get("budget")[0]
                    collaboration_with = data.get("collaborationWith")[0]

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
                        print("LEGIT EXTERNAL DETAILS SERIALIZER")
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
            "base": ProjectDetailSerializer(
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

        return details, documents, members

    def get(self, req, pk):
        proj = self.go(pk=pk)
        print(proj)
        ser = ProjectSerializer(proj).data
        details, documents, members = self.get_full_object(pk)
        # print(documents)
        return Response(
            {
                "project": ser,
                "details": details,
                "documents": documents,
                "members": members,
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

    def put(self, req, pk):
        proj = self.go(pk)
        ser = ProjectSerializer(
            proj,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uproj = ser.save()
            return Response(
                TinyProjectSerializer(uproj).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
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
        ser = ProjectMemberSerializer(
            data=req.data,
        )
        if ser.is_valid():
            # Set the is_leader field based on whether the user is the owner of the project
            project_id = req.data.get("project")
            user_id = req.data.get("user")
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                return Response(status=HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(status=HTTP_400_BAD_REQUEST)

            is_leader = user == project.owner
            member = ser.save(is_leader=is_leader)

            return Response(
                TinyProjectMemberSerializer(member).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(status=HTTP_400_BAD_REQUEST)


class ProjectMemberDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = ProjectMember.objects.get(pk=pk)
        except ProjectMember.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        team = self.go(pk)
        ser = ProjectMemberSerializer(team)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        team = self.go(pk)
        team.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        team = self.go(pk)
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
        ser = ProjectMemberSerializer(
            project_members,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
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
            obj = ProjectArea.objects.filter(project_id=pk).all()
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
