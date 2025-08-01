# region IMPORTS ==================================================

import ast
from collections import defaultdict
import datetime, json, os, re, subprocess, time, tempfile
from bs4 import BeautifulSoup
from operator import attrgetter
import bleach

from django.forms import ValidationError
from django.template.loader import render_to_string
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Prefetch, Max
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.cache import cache
from django.utils.html import strip_tags

from datetime import timedelta

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
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
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from agencies.models import BusinessArea, Division
from communications.models import Comment
from communications.serializers import (
    TinyCommentCreateSerializer,
    TinyCommentSerializer,
)
from config.helpers import get_encoded_image, send_email_with_embedded_image
from documents.templatetags.custom_filters import extract_text_content
from medias.models import (
    AECEndorsementPDF,
    AnnualReportMedia,
    AnnualReportPDF,
    LegacyAnnualReportPDF,
    ProjectDocumentPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
)
from medias.serializers import (
    AECPDFCreateSerializer,
    AnnualReportPDFCreateSerializer,
    AnnualReportPDFSerializer,
    ProjectDocumentPDFSerializer,
    TinyLegacyAnnualReportPDFSerializer,
    TinyMethodologyImageSerializer,
    TinyProjectPhotoSerializer,
)
from projects.models import Project, ProjectDetail, ProjectMember
from projects.serializers import ARExternalProjectSerializer, ProjectSerializer
from users.models import PublicStaffProfile, User, UserWork
from .models import (
    ConceptPlan,
    CustomPublication,
    ProgressReport,
    ProjectClosure,
    ProjectPlan,
    StudentReport,
    ProjectDocument,
    AnnualReport,
    Endorsement,
)
from .serializers import (
    AnnualReportSerializer,
    ConceptPlanCreateSerializer,
    ConceptPlanSerializer,
    CustomPublicationSerializer,
    EndorsementCreationSerializer,
    EndorsementSerializer,
    LibraryPublicationResponseSerializer,
    # LibraryResponseSerializer,
    MiniAnnualReportSerializer,
    MiniEndorsementSerializer,
    OptimisedProgressReportAnnualReportSerializer,
    OptimisedStudentReportAnnualReportSerializer,
    ProgressReportAnnualReportSerializer,
    ProgressReportCreateSerializer,
    ProgressReportSerializer,
    ProjectClosureCreationSerializer,
    ProjectClosureSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
    ProjectPlanCreateSerializer,
    ProjectPlanSerializer,
    PublicationResponseSerializer,
    StudentReportAnnualReportSerializer,
    StudentReportCreateSerializer,
    StudentReportSerializer,
    TinyAnnualReportSerializer,
    TinyConceptPlanSerializer,
    TinyEndorsementSerializer,
    TinyProgressReportSerializer,
    TinyProjectClosureSerializer,
    TinyProjectDocumentSerializer,
    TinyProjectPlanSerializer,
    TinyStudentReportSerializer,
)

# endregion ==================================================


def get_current_maintainer_pk():
    """
    Retrieves the primary key of the current maintainer set in AdminOptions.
    Returns None if no maintainer is set.
    """
    from adminoptions.models import AdminOptions

    admin_options = AdminOptions.objects.first()
    return (
        admin_options.maintainer.pk
        if admin_options and admin_options.maintainer
        else None
    )


# region REPORTS ==========================================================


class Reports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is viewing reports")
        all_reports = AnnualReport.objects.all()
        ser = TinyAnnualReportSerializer(
            all_reports,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def create_reports_for_eligible_projects(self, report_id, user):
        report = AnnualReport.objects.get(pk=report_id)

        settings.LOGGER.error(
            msg=f"{user} is BATCH Creating PROGRESS/STUDENT reports for eligible projects"
        )
        # Create progress reports
        eligible_projects = Project.objects.filter(
            Q(status__in=Project.ACTIVE_ONLY)
            & Q(
                kind__in=[
                    Project.CategoryKindChoices.SCIENCE,
                    Project.CategoryKindChoices.COREFUNCTION,
                ]
            )
            & Q(documents__kind=ProjectDocument.CategoryKindChoices.PROJECTPLAN)
            & Q(documents__status=ProjectDocument.StatusChoices.APPROVED)
        ).exclude(documents__progress_report_details__report__year=report.year)

        eligible_student_projects = Project.objects.filter(
            Q(status__in=Project.ACTIVE_ONLY)
            & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
        ).exclude(documents__progress_report_details__report__year=report.year)

        # Combine the two querysets
        all_eligible_projects = eligible_projects | eligible_student_projects

        for project in all_eligible_projects:
            if project.kind == Project.CategoryKindChoices.STUDENT:
                typeofdoc = ProjectDocument.CategoryKindChoices.STUDENTREPORT
            elif (
                project.kind == Project.CategoryKindChoices.SCIENCE
                or project.kind == Project.CategoryKindChoices.COREFUNCTION
            ):
                typeofdoc = ProjectDocument.CategoryKindChoices.PROGRESSREPORT
            new_doc_data = {
                "old_id": 1,
                "kind": typeofdoc,
                "status": "new",
                "modifier": user.pk,
                "creator": user.pk,
                "project": project.pk,
            }

            new_project_document = ProjectDocumentCreateSerializer(data=new_doc_data)

            if new_project_document.is_valid():
                with transaction.atomic():
                    doc = new_project_document.save()
                    if project.kind != Project.CategoryKindChoices.STUDENT:
                        progress_report_data = {
                            "document": doc.pk,
                            "project": project.pk,
                            "report": report.pk,
                            "project": project.pk,
                            "year": report.year,
                            "context": "<p></p>",
                            "implications": "<p></p>",
                            "future": "<p></p>",
                            "progress": "<p></p>",
                            "aims": "<p></p>",
                        }

                        progress_report = ProgressReportCreateSerializer(
                            data=progress_report_data
                        )

                        if progress_report.is_valid():
                            progress_report.save()
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                        else:
                            settings.LOGGER.error(msg=f"{progress_report.errors}")
                            return Response(
                                progress_report.errors, HTTP_400_BAD_REQUEST
                            )
                    else:
                        student_report_data = {
                            "document": doc.pk,
                            "project": project.pk,
                            "report": report.pk,
                            "project": project.pk,
                            "year": report.year,
                            "progress_report": "<p></p>",
                        }

                        progress_report = StudentReportCreateSerializer(
                            data=student_report_data
                        )

                        if progress_report.is_valid():
                            progress_report.save()
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                        else:
                            settings.LOGGER.error(msg=f"{progress_report.errors}")
                            return Response(
                                progress_report.errors, HTTP_400_BAD_REQUEST
                            )

            else:
                settings.LOGGER.error(msg=f"{new_project_document.errors}")
                return Response(new_project_document.errors, HTTP_400_BAD_REQUEST)

    def get_prepopulation_data_from_last_report(self, year):

        data_object = {
            "dm": "",
            "service_delivery_intro": "",
            "research_intro": "",
            "student_intro": "",
            "publications": "",
        }

        # Use the year parameter to search for the first AnnualReport that comes prior to the given year.
        # Whilst this sometimes may be the prior year, sometimes the prior year's report doesnt exist, so just get the year that is closest and which comes before.
        previous_year = AnnualReport.objects.filter(year__lt=year).aggregate(
            Max("year")
        )["year__max"]

        if previous_year is not None:
            # If there is a report from the previous year, fetch its data
            previous_report = AnnualReport.objects.get(year=previous_year)
            data_object["dm"] = previous_report.dm
            data_object["service_delivery_intro"] = (
                previous_report.service_delivery_intro
            )
            data_object["research_intro"] = previous_report.research_intro
            data_object["student_intro"] = previous_report.student_intro
            data_object["publications"] = previous_report.publications

        return data_object

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating a report.")
        year = req.data.get("year")
        date_open = req.data.get("date_open")
        date_closed = req.data.get("date_closed")

        creator = req.user.pk
        modifier = req.user.pk
        old_id = req.data.get("old_id", 1)

        creation_data = {
            "old_id": old_id,
            "year": year,
            "date_open": date_open,
            "date_closed": date_closed,
            "creator": creator,
            "modifier": modifier,
        }

        additional_data = self.get_prepopulation_data_from_last_report(year)

        creation_data.update(additional_data)

        ser = AnnualReportSerializer(
            data={**creation_data},
        )
        if ser.is_valid():
            with transaction.atomic():
                report = ser.save()
                should_seek_reports_now = req.data.get("seek_update")
                if should_seek_reports_now == True:
                    try:
                        self.create_reports_for_eligible_projects(
                            report_id=report.id, user=req.user
                        )
                    except Exception as e:
                        settings.LOGGER.error(msg=f"{e}")

                        return Response(
                            e,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyAnnualReportSerializer(report).data,
                    status=HTTP_201_CREATED,
                )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ReportDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        report = self.go(pk)
        ser = AnnualReportSerializer(
            report,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        report = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting report {report}")

        def delete_reports(report):
            reports = ProgressReport.objects.filter(report=report).all()
            for report in reports:
                report.document.delete()

        def delete_student_reports(report):
            reports = StudentReport.objects.filter(report=report).all()
            for report in reports:
                report.document.delete()

        delete_reports(report)
        delete_student_reports(report)
        report.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        report = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating report {report}")

        ser = AnnualReportSerializer(
            report,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            ureport = ser.save()
            return Response(
                TinyAnnualReportSerializer(ureport).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class GetLatestReportYear(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_year = AnnualReport.objects.aggregate(Max("year"))["year__max"]

        if latest_year is not None:
            latest_report = AnnualReport.objects.get(year=latest_year)
            serializer = AnnualReportSerializer(
                latest_report,
                context={"request": request},
            )
            return Response(
                serializer.data,
                status=HTTP_200_OK,
            )
        else:
            raise NotFound


class GetAvailableReportYearsForStudentReport(APIView):
    permission_classes = [IsAuthenticated]

    # Returns a list of serialized reports with the following:
    # year, report id
    # Only returns the years in which a progress report doesn't already exist for a given project
    def get(self, request, project_pk):
        if project_pk:
            all_student_reports = StudentReport.objects.filter(
                document__project_id=project_pk
            ).all()
            list_of_years_from_student_reports = list(
                set([report.year for report in all_student_reports])
            )
            all_annual_report_years = AnnualReport.objects.values_list(
                "year", flat=True
            ).distinct()

            available_years = list(
                set(all_annual_report_years) - set(list_of_years_from_student_reports)
            )
            available_reports = AnnualReport.objects.filter(year__in=available_years)

            serializer = MiniAnnualReportSerializer(
                available_reports,
                many=True,
                context={"request": request},
            )
            return Response(
                serializer.data,
                status=HTTP_200_OK,
            )
        else:
            raise NotFound


class GetAvailableReportYearsForProgressReport(APIView):
    permission_classes = [IsAuthenticated]

    # Returns a list of serialized reports with the following:
    # year, report id
    # Only returns the years in which a progress report doesn't already exist for a given project
    def get(self, request, project_pk):
        if project_pk:
            all_progress_reports = ProgressReport.objects.filter(
                document__project_id=project_pk
            ).all()
            list_of_years_from_progress_reports = list(
                set([report.year for report in all_progress_reports])
            )
            all_annual_report_years = AnnualReport.objects.values_list(
                "year", flat=True
            ).distinct()

            available_years = list(
                set(all_annual_report_years) - set(list_of_years_from_progress_reports)
            )
            available_reports = AnnualReport.objects.filter(year__in=available_years)

            serializer = MiniAnnualReportSerializer(
                available_reports,
                many=True,
                context={"request": request},
            )
            return Response(
                serializer.data,
                status=HTTP_200_OK,
            )
        else:
            raise NotFound


class GetWithoutPDFs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports_without_pdfs = AnnualReport.objects.exclude(pdf__isnull=False)

        if reports_without_pdfs:
            serializer = TinyAnnualReportSerializer(
                reports_without_pdfs,
                context={"request": request},
                many=True,
            )
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return None


class GetReportPDF(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            report_pdf_obj = AnnualReportPDF.objects.get(report=pk)
        except AnnualReportPDF.DoesNotExist:
            raise NotFound
        return report_pdf_obj

    def get(self, req, pk):
        pdf_object = self.go(pk=pk)
        ser = AnnualReportPDFSerializer(
            pdf_object,
        )
        # Convert the serialized data to a dictionary
        serialized_data = json.loads(json.dumps(ser.data, cls=DjangoJSONEncoder))

        # Include the PDF data in the serialized response
        serialized_data["pdf_data"] = ser.data.get("pdf_data")
        return Response(
            serialized_data,
            HTTP_200_OK,
        )


class GetWithPDFs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports_with_pdfs = AnnualReport.objects.exclude(pdf__isnull=True)

        # if reports_with_pdfs:
        serializer = TinyAnnualReportSerializer(
            reports_with_pdfs,
            context={"request": request},
            many=True,
        )
        return Response(serializer.data, status=HTTP_200_OK)


class GetLegacyPDFs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        legacy_items = LegacyAnnualReportPDF.objects.all()

        # if reports_with_pdfs:
        serializer = TinyLegacyAnnualReportPDFSerializer(
            legacy_items,
            context={"request": request},
            many=True,
        )
        return Response(serializer.data, status=HTTP_200_OK)


class GetCompletedReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        completed_reports = AnnualReport.objects.filter(is_published=True).all()
        if completed_reports:
            serializer = AnnualReportSerializer(
                completed_reports,
                context={"request": request},
                many=True,
            )
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return None


# endregion ==========================================================


# region Latest Year's Reports ==========================================================


class BeginAnnualReportDocGeneration(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound
        return report

    def post(self, req, pk):
        report_object = self.go(pk=pk)


class LatestYearsProgressReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"Getting Approved Progress Reports for current year")

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # print(latest_report)
            # Get progress report documents which belong to it and belong to active and approved projects
            active_docs = ProgressReport.objects.filter(
                Q(report=latest_report)
                & Q(document__status="approved")
                & (
                    Q(
                        project__business_area__division__name="Biodiversity and Conservation Science"
                    )
                    # | Q(
                    #     project__business_area__division__name="Dept Biodiversity, Conservation and Attractions"
                    # )
                )
            ).exclude(Q(project__business_area__division__name__isnull=True))
            ser = ProgressReportSerializer(
                active_docs, many=True, context={"request": req}
            )
            return Response(
                ser.data,
                HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


class LatestYearsStudentReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(
            msg=f"Getting Approved Student Reports for current year..."
        )

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # print(latest_report)
            # Get progress report documents which belong to it and belong to active and approved projects
            active_docs = StudentReport.objects.filter(
                Q(report=latest_report)
                & Q(document__status="approved")
                & (
                    Q(
                        project__business_area__division__name="Biodiversity and Conservation Science"
                    )
                    # | Q(
                    #     project__business_area__division__name="Dept Biodiversity, Conservation and Attractions"
                    # )
                )
            ).exclude(Q(project__business_area__division__name__isnull=True))
            ser = StudentReportSerializer(
                active_docs, many=True, context={"request": req}
            )
            return Response(
                ser.data,
                HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


class LatestYearsInactiveReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # Get progress report documents which belong to it and belong to active and approved projects
            inactive_srs = (
                StudentReport.objects.filter(
                    Q(report=latest_report)
                    & (
                        Q(
                            project__business_area__division__name="Biodiversity and Conservation Science"
                        )
                        # | Q(
                        #     project__business_area__division__name="Dept Biodiversity, Conservation and Attractions"
                        # )
                    )
                )
                .exclude(document__status__in=["approved"])
                .exclude(Q(project__business_area__division__name__isnull=True))
                .all()
            )
            inactive_prs = (
                ProgressReport.objects.filter(
                    Q(report=latest_report)
                    & (
                        Q(
                            project__business_area__division__name="Biodiversity and Conservation Science"
                        )
                        # | Q(
                        #     project__business_area__division__name="Dept Biodiversity, Conservation and Attractions"
                        # )
                    )
                )
                .exclude(document__status__in=["approved"])
                .exclude(Q(project__business_area__division__name__isnull=True))
                .all()
            )

            sr_ser = StudentReportSerializer(
                inactive_srs, many=True, context={"request": req}
            )
            pr_ser = ProgressReportSerializer(
                inactive_prs, many=True, context={"request": req}
            )

            res_dict = {
                "student_reports": sr_ser.data,
                "progress_reports": pr_ser.data,
            }

            return Response(
                res_dict,
                HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


class FullLatestReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):

        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            ser = AnnualReportSerializer(
                latest_report,
                context={"request": req},
            )
            return Response(
                ser.data,
                status=HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


# endregion ==================================================

# region PROJECT DOCUMENTS ==============================================


class ProjectDocuments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_projects = ProjectDocument.objects.all()
        ser = TinyProjectDocumentSerializer(
            all_projects,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is Creating Project Document for project {req.data.get('project')}"
        )
        kind = req.data.get("kind")
        project_pk = req.data.get("project")
        project_kind = req.data.get("projectKind")

        data = {
            "old_id": 1,
            "kind": kind,
            "status": ProjectDocument.StatusChoices.NEW,
            "project": project_pk,
            "creator": req.user.pk,
            "modifier": req.user.pk,
        }

        if kind == "projectclosure" and project_kind and project_kind != "science":
            data["project_lead_approval_granted"] = True
            data["business_area_lead_approval_granted"] = True
            data["directorate_approval_granted"] = True
            data["status"] = ProjectDocument.StatusChoices.APPROVED

        document_serializer = ProjectDocumentCreateSerializer(data=data)

        if document_serializer.is_valid():
            with transaction.atomic():
                doc = document_serializer.save()
                if kind == "concept":
                    project = req.data.get("project")
                    concept_plan_data_object = {
                        "document": doc.pk,
                        "project": project,
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
                            if req.data.get("staff_time_allocation") is not None
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
                            concplan = concept_plan_serializer.save()
                        except Exception as e:
                            settings.LOGGER.error(msg=f"concept Plan error: {e}")

                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        settings.LOGGER.error(msg=f"{project_plan_serializer.errors}")
                        return Response(
                            project_plan_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                elif kind == "projectplan":
                    project = int(req.data.get("project"))
                    project_plan_data_object = {
                        "document": doc.pk,
                        "project": project,
                        "background": (
                            req.data.get("background")
                            if req.data.get("background") is not None
                            else "<p></p>"
                        ),
                        "methodology": (
                            req.data.get("methodology")
                            if req.data.get("methodology") is not None
                            else "<p></p>"
                        ),
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
                        "knowledge_transfer": (
                            req.data.get("knowledge_transfer")
                            if req.data.get("knowledge_transfer") is not None
                            else "<p></p>"
                        ),
                        "listed_references": (
                            req.data.get("listed_references")
                            if req.data.get("listed_references") is not None
                            else "<p></p>"
                        ),
                        "operating_budget": (
                            req.data.get("operating_budget")
                            if req.data.get("operating_budget") is not None
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
                        "operating_budget_external": (
                            req.data.get("operating_budget_external")
                            if req.data.get("operating_budget_external") is not None
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
                        "related_projects": (
                            req.data.get("related_projects")
                            if req.data.get("related_projects") is not None
                            else "<p></p>"
                        ),
                    }
                    project_plan_serializer = ProjectPlanCreateSerializer(
                        data=project_plan_data_object
                    )

                    if project_plan_serializer.is_valid():
                        try:
                            projplan = project_plan_serializer.save()
                            endorsements = EndorsementCreationSerializer(
                                data={
                                    "project_plan": projplan.pk,
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

                        except Exception as e:
                            settings.LOGGER.error(msg=f"{e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        settings.LOGGER.error(msg=f"{project_plan_serializer.errors}")
                        return Response(
                            project_plan_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )
                elif kind == "projectclosure":
                    reason = req.data.get("reason")
                    outcome = req.data.get("outcome")
                    project = req.data.get("project")

                    closure_data_object = {
                        "document": doc.pk,
                        "project": project,
                        "intended_outcome": outcome,
                        "reason": reason,
                        "scientific_outputs": (
                            req.data.get("scientific_outputs")
                            if req.data.get("scientific_outputs") is not None
                            else "<p></p>"
                        ),
                        "knowledge_transfer": (
                            req.data.get("knowledge_transfer")
                            if req.data.get("knowledge_transfer") is not None
                            else "<p></p>"
                        ),
                        "data_location": (
                            req.data.get("data_location")
                            if req.data.get("data_location") is not None
                            else "<p></p>"
                        ),
                        "hardcopy_location": (
                            req.data.get("hardcopy_location")
                            if req.data.get("hardcopy_location") is not None
                            else "<p></p>"
                        ),
                        "backup_location": (
                            req.data.get("backup_location")
                            if req.data.get("backup_location") is not None
                            else "<p></p>"
                        ),
                    }

                    closure_serializer = ProjectClosureCreationSerializer(
                        data=closure_data_object
                    )

                    if closure_serializer.is_valid():
                        try:
                            with transaction.atomic():
                                closure = closure_serializer.save()
                                if (
                                    kind == "projectclosure"
                                    and project_kind
                                    and project_kind != "science"
                                ):
                                    closure.document.project.status = outcome
                                else:
                                    closure.document.project.status = (
                                        "closure_requested"
                                    )
                                closure.document.project.save()

                        except Exception as e:
                            settings.LOGGER.error(msg=f"{e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        settings.LOGGER.error(msg=f"{closure_serializer.errors}")
                        return Response(
                            closure_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )
                elif kind == "progressreport":
                    report_id = req.data.get("report")
                    year = req.data.get("year")
                    project = req.data.get("project")

                    def get_prepopulation_data_from_last_report(year, project):
                        data_object = {
                            "context": "",
                            "aims": "",
                            "progress": "",
                            "implications": "",
                            "future": "",
                        }

                        # Use the year parameter to search for the first ProgressReport that comes prior to the given year.
                        # Whilst this sometimes may be the prior year, sometimes the prior year's report doesnt exist, so just get the year that is closest and which comes before.
                        progress_reports_for_this_project = (
                            ProgressReport.objects.filter(project=project).all()
                        )
                        previous_year = progress_reports_for_this_project.filter(
                            year__lt=year
                        ).aggregate(Max("year"))["year__max"]

                        print(previous_year)

                        if previous_year is not None:
                            # If there is a report from the previous year, fetch its data
                            previous_report = progress_reports_for_this_project.get(
                                year=previous_year
                            )
                            print(previous_report)
                            data_object["context"] = previous_report.context
                            data_object["aims"] = previous_report.aims
                            data_object["progress"] = previous_report.progress
                            data_object["implications"] = previous_report.implications
                            data_object["future"] = previous_report.future

                        return data_object

                    last_reports_data = get_prepopulation_data_from_last_report(
                        year, project
                    )

                    progress_report_data_object = {
                        "document": doc.pk,
                        "report": report_id,
                        "project": project,
                        "year": year,
                        "context": last_reports_data["context"],
                        "implications": last_reports_data["implications"],
                        "future": last_reports_data["future"],
                        "progress": last_reports_data["progress"],
                        "aims": last_reports_data["aims"],
                        "is_final_report": (
                            req.data.get("is_final_report")
                            if req.data.get("is_final_report") is not None
                            else False
                        ),
                    }

                    pr_serializer = ProgressReportCreateSerializer(
                        data=progress_report_data_object
                    )

                    if pr_serializer.is_valid():
                        try:
                            with transaction.atomic():
                                progress_report = pr_serializer.save()
                                progress_report.document.project.status = "updating"
                                progress_report.document.project.save()

                        except Exception as e:
                            settings.LOGGER.error(f"Progress Report save error: {e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        settings.LOGGER.error(msg=f"{pr_serializer.errors}")
                        return Response(
                            pr_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                elif kind == "studentreport":
                    project = req.data.get("project")
                    report_id = req.data.get("report")
                    report = AnnualReport.objects.get(pk=report_id)

                    def get_prepopulation_data_from_last_report(year, project):
                        data_object = {
                            "progress_report": "",
                        }

                        # Use the year parameter to search for the first ProgressReport that comes prior to the given year.
                        # Whilst this sometimes may be the prior year, sometimes the prior year's report doesnt exist, so just get the year that is closest and which comes before.
                        student_reports_for_this_project = StudentReport.objects.filter(
                            project=project
                        ).all()
                        previous_year = student_reports_for_this_project.filter(
                            year__lt=year
                        ).aggregate(Max("year"))["year__max"]

                        print(previous_year)

                        if previous_year is not None:
                            # If there is a report from the previous year, fetch its data
                            previous_report = student_reports_for_this_project.get(
                                year=previous_year
                            )
                            print(previous_report)
                            data_object["progress_report"] = (
                                previous_report.progress_report
                            )

                        return data_object

                    last_reports_data = get_prepopulation_data_from_last_report(
                        report.year, project
                    )

                    student_report_data_object = {
                        "document": doc.pk,
                        "report": report.pk,
                        "project": project,
                        "year": report.year,
                        "progress_report": last_reports_data["progress_report"],
                    }
                    print(student_report_data_object)
                    sr_serializer = StudentReportCreateSerializer(
                        data=student_report_data_object
                    )

                    if sr_serializer.is_valid():
                        try:
                            with transaction.atomic():
                                student_report = sr_serializer.save()
                                student_report.document.project.status = "updating"
                                student_report.document.project.save()

                        except Exception as e:
                            settings.LOGGER.error(msg=f"{e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        settings.LOGGER.error(sr_serializer.errors)
                        return Response(
                            sr_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyProjectDocumentSerializer(doc).data,
                    status=HTTP_201_CREATED,
                )
        else:
            settings.LOGGER.error(msg=f"{document_serializer.errors}")
            return Response(
                document_serializer.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProjectDocumentDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        project_document = self.go(pk)
        ser = ProjectDocumentSerializer(
            project_document,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        project_document = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting {project_document}")
        project_document.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        project_document = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating {project_document}")
        ser = ProjectDocumentSerializer(
            project_document,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_project_document = ser.save()
            return Response(
                TinyProjectDocumentSerializer(u_project_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class ProjectDocsPendingMyActionStageOne(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting docs pending stage 1 action")
        member_input_required = []
        pl_input_required = []
        active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY).all()

        # Lead Filtering
        all_leader_memberships = []
        all_memberships = []
        for project in active_projects:
            membership = ProjectMember.objects.filter(project=project, user=req.user)
            if membership.exists():
                all_memberships.append(membership.first())
                lead_membership = membership.filter(is_leader=True)
                if lead_membership.exists():
                    all_leader_memberships.append(lead_membership.first())
        if len(all_memberships) >= 1:
            for membershipp in all_memberships:
                related_project = membershipp.project
                if related_project in active_projects:
                    if membershipp in all_leader_memberships:
                        # Handle lead membership
                        project_docs_without_lead_approval = (
                            ProjectDocument.objects.filter(
                                project=related_project,
                                project_lead_approval_granted=False,
                            ).exclude(status=ProjectDocument.StatusChoices.APPROVED)
                        )
                        for doc in project_docs_without_lead_approval:
                            pl_input_required.append(doc)
                    else:
                        # Handle ordinary membership
                        project_docs_requiring_member_input = (
                            ProjectDocument.objects.filter(
                                project=related_project,
                                project_lead_approval_granted=False,
                            ).exclude(status=ProjectDocument.StatusChoices.APPROVED)
                        )
                        for doc in project_docs_requiring_member_input:
                            member_input_required.append(doc)

        filtered_pm_input_required = list(
            {doc.id: doc for doc in member_input_required}.values()
        )
        filtered_pl_input_required = list(
            {doc.id: doc for doc in pl_input_required}.values()
        )

        data = {
            "team": TinyProjectDocumentSerializer(
                filtered_pm_input_required,
                many=True,
                context={"request": req},
            ).data,
            "lead": TinyProjectDocumentSerializer(
                filtered_pl_input_required,
                many=True,
                context={"request": req},
            ).data,
        }

        return Response(
            data,
            status=HTTP_200_OK,
        )


class ProjectDocsPendingMyActionStageTwo(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting docs pending stage 2 action")
        ba_input_required = []

        active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY).all()

        # Business Area Lead Task Filtering
        for project in active_projects:
            if project.business_area != None:
                ba_id = project.business_area.leader.id
                if ba_id == req.user.id:
                    is_business_area_lead = True
                else:
                    is_business_area_lead = False
                if is_business_area_lead == True:
                    projects_docs = (
                        ProjectDocument.objects.filter(project=project)
                        .exclude(status=ProjectDocument.StatusChoices.APPROVED)
                        .all()
                    )
                    for doc in projects_docs:
                        if (doc.project_lead_approval_granted == True) and (
                            doc.business_area_lead_approval_granted == False
                        ):
                            ba_input_required.append(doc)
            else:
                # Create a temporary file
                temp_dir = (
                    tempfile.gettempdir()
                )  # Use the system temp directory or customize
                temp_file_path = os.path.join(temp_dir, "activeProjectsWithoutBAs.txt")

                with open(temp_file_path, "a+") as temp_file:
                    temp_file.seek(0)  # Move to the start of the file to read
                    existing_content = temp_file.read()  # Read the existing content

                    # Check if the content already exists before writing
                    if f"{project.pk} | {project.title}\n" not in existing_content:
                        temp_file.write(f"{project.pk} | {project.title}\n")
                        temp_file.flush()  # Ensure content is written to disk

                print(f"File saved to: {temp_file_path}")

        filtered_ba_input_required = list(
            {doc.id: doc for doc in ba_input_required}.values()
        )

        data = {
            "ba": TinyProjectDocumentSerializer(
                filtered_ba_input_required,
                many=True,
                context={"request": req},
            ).data,
        }

        return Response(
            data,
            status=HTTP_200_OK,
        )


class ProjectDocsPendingMyActionStageThree(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting docs pending stage 3 action")
        documents = []
        member_input_required = []
        pl_input_required = []
        ba_input_required = []
        directorate_input_required = []

        user_work = UserWork.objects.get(user=req.user.pk)
        active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY).all()

        # Business Area Lead Task Filtering
        for project in active_projects:
            if project.business_area != None:
                ba_id = project.business_area.leader.id
                if ba_id == req.user.id:
                    is_business_area_lead = True
                else:
                    is_business_area_lead = False
                if is_business_area_lead == True:
                    projects_docs = (
                        ProjectDocument.objects.filter(project=project)
                        .exclude(status=ProjectDocument.StatusChoices.APPROVED)
                        .all()
                    )
                    for doc in projects_docs:
                        if (doc.project_lead_approval_granted == True) and (
                            doc.business_area_lead_approval_granted == False
                        ):
                            documents.append(doc)
                            ba_input_required.append(doc)
            else:
                # Create a temporary file
                temp_dir = (
                    tempfile.gettempdir()
                )  # Use the system temp directory or customize
                temp_file_path = os.path.join(temp_dir, "activeProjectsWithoutBAs.txt")

                with open(temp_file_path, "a+") as temp_file:
                    temp_file.seek(0)  # Move to the start of the file to read
                    existing_content = temp_file.read()  # Read the existing content

                    # Check if the content already exists before writing
                    if f"{project.pk} | {project.title}\n" not in existing_content:
                        temp_file.write(f"{project.pk} | {project.title}\n")
                        temp_file.flush()  # Ensure content is written to disk

                print(f"File saved to: {temp_file_path}")
        # Directorate Filtering
        if user_work.business_area is not None:
            is_directorate = user_work.business_area.name == "Directorate"
        else:
            is_directorate = False
        if is_directorate:
            for project in active_projects:
                projects_docs = (
                    ProjectDocument.objects.filter(project=project)
                    .exclude(status=ProjectDocument.StatusChoices.APPROVED)
                    .all()
                )
                for doc in projects_docs:
                    if (doc.business_area_lead_approval_granted == True) and (
                        doc.directorate_approval_granted == False
                    ):
                        documents.append(doc)
                        directorate_input_required.append(doc)

        # Lead Filtering
        all_leader_memberships = []
        all_memberships = []
        for project in active_projects:
            membership = ProjectMember.objects.filter(project=project, user=req.user)
            if membership.exists():
                all_memberships.append(membership.first())
                lead_membership = membership.filter(is_leader=True)
                if lead_membership.exists():
                    all_leader_memberships.append(lead_membership.first())
        if len(all_memberships) >= 1:
            for membershipp in all_memberships:
                related_project = membershipp.project
                if related_project in active_projects:
                    if membershipp in all_leader_memberships:
                        # Handle lead membership
                        project_docs_without_lead_approval = (
                            ProjectDocument.objects.filter(
                                project=related_project,
                                project_lead_approval_granted=False,
                            ).exclude(status=ProjectDocument.StatusChoices.APPROVED)
                        )
                        for doc in project_docs_without_lead_approval:
                            documents.append(doc)
                            pl_input_required.append(doc)
                    else:
                        # Handle ordinary membership
                        project_docs_requiring_member_input = (
                            ProjectDocument.objects.filter(
                                project=related_project,
                                project_lead_approval_granted=False,
                            ).exclude(status=ProjectDocument.StatusChoices.APPROVED)
                        )
                        for doc in project_docs_requiring_member_input:
                            documents.append(doc)
                            member_input_required.append(doc)

        filtered_documents = list({doc.id: doc for doc in documents}.values())
        filtered_pm_input_required = list(
            {doc.id: doc for doc in member_input_required}.values()
        )
        filtered_pl_input_required = list(
            {doc.id: doc for doc in pl_input_required}.values()
        )
        filtered_ba_input_required = list(
            {doc.id: doc for doc in ba_input_required}.values()
        )
        filtered_directorate_input_required = list(
            {doc.id: doc for doc in directorate_input_required}.values()
        )

        ser = TinyProjectDocumentSerializer(
            filtered_documents,
            many=True,
            context={"request": req},
        )

        data = {
            "all": ser.data,
            "team": TinyProjectDocumentSerializer(
                filtered_pm_input_required,
                many=True,
                context={"request": req},
            ).data,
            "lead": TinyProjectDocumentSerializer(
                filtered_pl_input_required,
                many=True,
                context={"request": req},
            ).data,
            "ba": TinyProjectDocumentSerializer(
                filtered_ba_input_required,
                many=True,
                context={"request": req},
            ).data,
            "directorate": TinyProjectDocumentSerializer(
                filtered_directorate_input_required,
                many=True,
                context={"request": req},
            ).data,
        }

        return Response(
            data,
            status=HTTP_200_OK,
        )


class ProjectDocsPendingMyActionAllStages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is getting their documents pending action"
        )
        documents = []
        member_input_required = []
        pl_input_required = []
        ba_input_required = []
        directorate_input_required = []

        # Optimise this query with select_related
        small_user_object = (
            User.objects.filter(pk=req.user.pk)
            .select_related("work", "work__business_area")
            .prefetch_related("business_areas_led")
            .first()
        )

        if small_user_object:
            ba = small_user_object.work.business_area
            is_directorate = (
                ba != None and ba.name == "Directorate"
            ) or req.user.is_superuser

            active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY).all()

            # Check if the user is a leader of any business area
            business_areas_led = small_user_object.business_areas_led.values_list(
                "id", flat=True
            )

            is_ba_leader = len(business_areas_led) >= 1

            if is_ba_leader:
                # filter further for only projects which the user leads
                ba_projects = active_projects.filter(
                    business_area__pk__in=business_areas_led
                ).all()

                # Extract project IDs for Business Area
                ba_project_ids = ba_projects.values_list("id", flat=True)

                # Fetch all documents requiring BA attention with optimised relationships
                docs_requiring_ba_attention = (
                    ProjectDocument.objects.exclude(
                        status=ProjectDocument.StatusChoices.APPROVED
                    )
                    .filter(
                        project__in=ba_project_ids,
                        project_lead_approval_granted=True,
                        business_area_lead_approval_granted=False,
                    )
                    .select_related(
                        "project",
                        "project__business_area",
                        "project__business_area__image",
                        "project__business_area__division",
                        "project__business_area__division__director",
                        "project__business_area__division__approver",
                        "project__business_area__leader",
                        "project__business_area__caretaker",
                        "project__business_area__finance_admin",
                        "project__business_area__data_custodian",
                        "project__image",
                        "project__image__uploader",
                        "pdf",
                        "pdf__document",
                        "pdf__project",
                        "creator",
                        "modifier",
                    )
                    .prefetch_related(
                        "project__business_area__division__directorate_email_list",
                    )
                    .all()
                )

                # Append the documents to the respective lists
                documents.extend(docs_requiring_ba_attention)
                ba_input_required.extend(docs_requiring_ba_attention)

            # Directorate Filtering
            if is_directorate:
                # Extract project IDs for Directorate
                directorate_project_ids = active_projects.values_list("id", flat=True)

                # Fetch all documents requiring Directorate attention with optimised relationships
                docs_requiring_directorate_attention = (
                    ProjectDocument.objects.exclude(
                        status=ProjectDocument.StatusChoices.APPROVED
                    )
                    .filter(
                        project__in=directorate_project_ids,
                        business_area_lead_approval_granted=True,
                        directorate_approval_granted=False,
                    )
                    .select_related(
                        "project",
                        "project__business_area",
                        "project__business_area__image",
                        "project__business_area__division",
                        "project__business_area__division__director",
                        "project__business_area__division__approver",
                        "project__business_area__leader",
                        "project__business_area__caretaker",
                        "project__business_area__finance_admin",
                        "project__business_area__data_custodian",
                        "project__image",
                        "project__image__uploader",
                        "pdf",
                        "pdf__document",
                        "pdf__project",
                        "creator",
                        "modifier",
                    )
                    .prefetch_related(
                        "project__business_area__division__directorate_email_list",
                    )
                    .all()
                )

                # Append the documents to the respective lists
                documents.extend(docs_requiring_directorate_attention)
                directorate_input_required.extend(docs_requiring_directorate_attention)

            # Lead Filtering - optimised the membership query
            all_leader_memberships = ProjectMember.objects.filter(
                project__in=active_projects, user=small_user_object, is_leader=True
            ).select_related("project")

            # Extract project IDs for projects where the user is a lead
            lead_project_ids = [
                membership.project_id for membership in all_leader_memberships
            ]

            # Fetch all documents requiring lead attention with optimised relationships
            docs_requiring_lead_attention = (
                ProjectDocument.objects.exclude(
                    status=ProjectDocument.StatusChoices.APPROVED
                )
                .filter(
                    project__in=lead_project_ids,
                    project_lead_approval_granted=False,
                )
                .select_related(
                    "project",
                    "project__business_area",
                    "project__business_area__image",
                    "project__business_area__division",
                    "project__business_area__division__director",
                    "project__business_area__division__approver",
                    "project__business_area__leader",
                    "project__business_area__caretaker",
                    "project__business_area__finance_admin",
                    "project__business_area__data_custodian",
                    "project__image",
                    "project__image__uploader",
                    "pdf",
                    "pdf__document",
                    "pdf__project",
                    "creator",
                    "modifier",
                )
                .prefetch_related(
                    "project__business_area__division__directorate_email_list",
                )
                .all()
            )

            # Separate the documents based on lead and member input
            for doc in docs_requiring_lead_attention:
                documents.append(doc)
                if doc.project_id in lead_project_ids:
                    pl_input_required.append(doc)

            # Optimised this query too (N+1)
            my_non_leader_memberships = (
                ProjectMember.objects.filter(user=req.user, is_leader=False)
                .select_related("project")
                .all()
            )

            my_projects = [
                membership.project for membership in my_non_leader_memberships
            ]

            docs_requiring_team_attention = (
                ProjectDocument.objects.exclude(
                    status=ProjectDocument.StatusChoices.APPROVED
                )
                .filter(project_lead_approval_granted=False, project__in=my_projects)
                .select_related(
                    "project",
                    "project__business_area",
                    "project__business_area__image",
                    "project__business_area__division",
                    "project__business_area__division__director",
                    "project__business_area__division__approver",
                    "project__business_area__leader",
                    "project__business_area__caretaker",
                    "project__business_area__finance_admin",
                    "project__business_area__data_custodian",
                    "project__image",
                    "project__image__uploader",
                    "pdf",
                    "pdf__document",
                    "pdf__project",
                    "creator",
                    "modifier",
                )
                .prefetch_related(
                    "project__business_area__division__directorate_email_list",
                )
                .all()
            )

            for doc in docs_requiring_team_attention:
                documents.append(doc)
                member_input_required.append(doc)

            filtered_documents = list({doc.id: doc for doc in documents}.values())
            filtered_pm_input_required = list(
                {doc.id: doc for doc in member_input_required}.values()
            )
            filtered_pl_input_required = list(
                {doc.id: doc for doc in pl_input_required}.values()
            )
            filtered_ba_input_required = list(
                {doc.id: doc for doc in ba_input_required}.values()
            )
            filtered_directorate_input_required = list(
                {doc.id: doc for doc in directorate_input_required}.values()
            )

            ser = TinyProjectDocumentSerializer(
                filtered_documents,
                many=True,
                context={"request": req},
            )

            data = {
                "all": ser.data,
                "team": TinyProjectDocumentSerializer(
                    filtered_pm_input_required,
                    many=True,
                    context={"request": req},
                ).data,
                "lead": TinyProjectDocumentSerializer(
                    filtered_pl_input_required,
                    many=True,
                    context={"request": req},
                ).data,
                "ba": TinyProjectDocumentSerializer(
                    filtered_ba_input_required,
                    many=True,
                    context={"request": req},
                ).data,
                "directorate": TinyProjectDocumentSerializer(
                    filtered_directorate_input_required,
                    many=True,
                    context={"request": req},
                ).data,
            }

            return Response(
                data,
                status=HTTP_200_OK,
            )
        else:
            data = {"all": [], "team": [], "lead": [], "ba": [], "directorate": []}
            return Response(
                data,
                status=HTTP_200_OK,
            )


class ProjectDocumentComments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req, pk):
        comments = Comment.objects.filter(document_id=pk).all()
        comments = comments.order_by("-updated_at", "-created_at")

        ser = TinyCommentSerializer(
            comments,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def sanitize_html(self, html_content):
        """
        Sanitize HTML content while preserving mention data attributes and safely handling CSS
        """
        if not html_content:
            return ""

        # Import CSS sanitizer
        from bleach.css_sanitizer import CSSSanitizer

        # Define allowed tags and attributes
        allowed_tags = [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "code",
            "em",
            "i",
            "li",
            "ol",
            "p",
            "strong",
            "ul",
            "br",
            "div",
            "span",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        ]

        allowed_attributes = {
            "*": ["class"],
            "a": ["href", "title", "target"],
            "span": [
                "data-user-id",
                "data-user-email",
                "data-user-name",
                "data-lexical-mention",
                "class",
                "style",  # We'll sanitize this with the CSS sanitizer
            ],
            "th": ["colspan", "rowspan"],
            "td": ["colspan", "rowspan"],
            # Add style to any element that might need it for mentions
            "div": ["style"],
            "p": ["style"],
        }

        # Define allowed CSS properties (specifically for mentions)
        allowed_css_properties = [
            "background-color",
            "color",
            "padding-left",
            "padding-right",
            "border-radius",
            "font-weight",
        ]

        # Create a CSS sanitizer with our allowed properties
        css_sanitizer = CSSSanitizer(
            allowed_css_properties=allowed_css_properties,
            allowed_svg_properties=[],
        )

        # Clean the HTML while preserving the allowed tags and attributes
        clean_html = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            css_sanitizer=css_sanitizer,
            strip=True,
        )

        return clean_html

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is trying to post a comment to doc {pk}:\n{extract_text_content(req.data['payload'])}"
        )

        sanitized_payload = self.sanitize_html(req.data["payload"])

        ser = TinyCommentCreateSerializer(
            data={
                "document": pk,
                "text": sanitized_payload,
                # "text": req.data["payload"],
                "user": req.data["user"],
            },
            context={"request": req},
        )
        if ser.is_valid():
            ser.save()
            return Response(
                ser.data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"FAIL: {ser.errors}")
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class DocumentSpawner(APIView):
    def post(self, req):
        kind = req.kind
        ser = ProjectDocumentSerializer(
            data={"kind": kind, "status": "new", "project": req.project}
        )
        settings.LOGGER.info(msg=f"{req.user} is spawning document")
        if ser.is_valid():
            with transaction.atomic():
                try:
                    project_document = ser.save()
                except Exception as e:
                    settings.LOGGER.error(msg=f"{e}")
                    return Response(e, HTTP_400_BAD_REQUEST)
                else:
                    doc_pk = project_document.pk
                    if kind == "concept":
                        pass
                    elif kind == "projectplan":
                        pass
                    elif kind == "progressreport":
                        pass
                    elif kind == "studentreport":
                        pass
                    elif kind == "projectclosure":
                        pass
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class GetPreviousReportsData(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        project_pk = req.data["project_pk"]
        doc_kind = req.data["writeable_document_kind"]
        section = req.data["section"]

        if doc_kind == "Progress Report":
            documents_of_type_from_project = ProgressReport.objects.filter(
                project=project_pk
            ).order_by("-year")
        elif doc_kind == "Student Report":
            documents_of_type_from_project = StudentReport.objects.filter(
                project=project_pk
            ).order_by("-year")
        else:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Check if there are at least two documents (IE can actually prepopulate with prior data)
        if documents_of_type_from_project.count() < 2:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Get the second-to-last document
        second_last_one = documents_of_type_from_project[1]

        # Get the specified section data
        try:
            section_data = getattr(second_last_one, section)
        except AttributeError:
            return Response(status=HTTP_400_BAD_REQUEST)

        return Response(data=section_data, status=HTTP_200_OK)


# endregion ==========================================

# region Concept Plans ====================================================================================================


class ConceptPlans(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_concept_plans = ConceptPlan.objects.all()
        ser = TinyConceptPlanSerializer(
            all_concept_plans,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = ConceptPlanSerializer(
            data=req.data,
        )
        settings.LOGGER.info(msg=f"{req.user} is posting a new concept plan")
        if ser.is_valid():
            concept_plan = ser.save()
            return Response(
                TinyConceptPlanSerializer(concept_plan).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ConceptPlanDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ConceptPlan.objects.get(pk=pk)
        except ConceptPlan.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        concept_plan = self.go(pk)
        ser = ConceptPlanSerializer(
            concept_plan,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        concept_plan = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting concept plan {concept_plan}")
        concept_plan.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        concept_plan = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating concept plan {concept_plan}")
        ser = ConceptPlanSerializer(
            concept_plan,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_concept_plan = ser.save()
            u_concept_plan.document.modifier = req.user
            u_concept_plan.document.save()

            return Response(
                TinyConceptPlanSerializer(u_concept_plan).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class GetConceptPlanData(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            concept_plan_data = ConceptPlan.objects.get(pk=pk)  # document
        except ConceptPlan.DoesNotExist:
            raise NotFound
        return concept_plan_data

    def post(self, req, pk):

        def timing_wrapper(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f"{func.__name__} took {elapsed_time:.6f} seconds to run.")
                return result

            return wrapper

        # STEP 1: Get Concept Plan Data
        def get_concept_plan_data():
            concept_plan_data = self.go(pk=pk)
            print(concept_plan_data)

            document_tag = f"CF-{concept_plan_data.project.year}-{concept_plan_data.project.number}"
            project_title = concept_plan_data.project.title
            project_status = concept_plan_data.project.status
            business_area_name = concept_plan_data.project.business_area.name

            def get_project_team(project_pk):
                # Get the member objects
                members = ProjectMember.objects.filter(project=project_pk).all()

                # Separate leader and other members
                leader = None
                other_members = []

                for member in members:
                    if member.is_leader:
                        leader = member
                    else:
                        other_members.append(member)

                # Sort other members based on their position value
                sorted_members = sorted(other_members, key=attrgetter("position"))

                # Create team_name_array with leader at the beginning and then other members
                team_name_array = []
                if leader:
                    team_name_array.append(
                        f"{leader.user.display_first_name} {leader.user.display_last_name}"
                    )

                for member in sorted_members:
                    team_name_array.append(
                        f"{member.user.display_first_name} {member.user.display_last_name}"
                    )

                return team_name_array

            project_team = get_project_team(concept_plan_data.project.pk)

            def get_project_image(project_pk):
                try:
                    image = ProjectPhoto.objects.get(project=project_pk)
                except ProjectPhoto.DoesNotExist:
                    return None
                return image

            project_image = TinyProjectPhotoSerializer(
                get_project_image(concept_plan_data.project.pk)
            ).data

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                concept_plan_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                concept_plan_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                concept_plan_data.document.directorate_approval_granted
            )

            def replace_json_string_with_html_table(input_string):
                try:
                    # Attempt to parse the input JSON string
                    data = json.loads(input_string)
                except json.JSONDecodeError:
                    # If parsing fails, return the original input string
                    return input_string

                # Begin constructing the HTML table with additional styling
                html_table = '<table class="table-light">\n  <colgroup>\n'
                html_table += '    <col style="background-color: rgb(242, 243, 245);">\n'  # Style for the leftmost column

                for _ in range(len(data[0])):
                    html_table += "    <col>\n"

                html_table += "  </colgroup>\n  <tbody>\n"

                for i, row in enumerate(data):
                    html_table += "    <tr>\n"
                    for j, cell in enumerate(row):
                        if i == 0:
                            # Apply background color to the first row
                            html_table += f'      <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\n'
                        elif j == 0:
                            # Apply background color to the leftmost column
                            html_table += f'      <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\n'
                        else:
                            html_table += f'      <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;">\n'

                        html_table += f'        <p class="editor-p-light" dir="ltr">\n'
                        html_table += f'          <span style="white-space: pre-wrap;">{cell}</span>\n'
                        html_table += f"        </p>\n"
                        html_table += "      </" + ("th" if i == 0 else "td") + ">\n"

                    html_table += "    </tr>\n"

                # Close the table
                html_table += "  </tbody>\n</table>"
                print(html_table)

                return html_table

            background = concept_plan_data.background
            aims = concept_plan_data.aims
            expected_outcomes = concept_plan_data.outcome
            collaborations = concept_plan_data.collaborations
            strategic_context = concept_plan_data.strategic_context
            staff_time_allocation = replace_json_string_with_html_table(
                concept_plan_data.staff_time_allocation
            )
            indicative_operating_budget = replace_json_string_with_html_table(
                concept_plan_data.budget
            )
            return {
                "concept_plan_data_pk": concept_plan_data.pk,
                "document_pk": concept_plan_data.document.pk,
                "project_pk": concept_plan_data.project.pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
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
            }

        timed_func = timing_wrapper(get_concept_plan_data)
        data = timed_func()

        return Response(
            data,
            HTTP_200_OK,
        )


# endregion Concept Plans ====================================================================================================

# region Project Plans ====================================================================================================


class ProjectPlans(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_project_plans = ProjectPlan.objects.all()
        ser = TinyProjectPlanSerializer(
            all_project_plans,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = ProjectPlanSerializer(
            data=req.data,
        )
        settings.LOGGER.info(msg=f"{req.user} is posting a new project plan")
        if ser.is_valid():
            project_plan = ser.save()
            return Response(
                TinyProjectPlanSerializer(project_plan).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProjectPlanDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        project_plan = self.go(pk)
        ser = ProjectPlanSerializer(
            project_plan,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is deleting project plan details for {pk}"
        )
        project_plan = self.go(pk)
        project_plan.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is updating project plan details for project plan id: {pk}"
        )
        if (
            "data_management" in req.data
            or "specimens" in req.data
            or "involves_animals" in req.data
            or "involves_plants" in req.data
        ):
            endorsement_to_edit = Endorsement.objects.filter(project_plan=pk).first()
            if "specimens" in req.data:
                specimen_value = req.data["specimens"]
                endorsement_to_edit.no_specimens = specimen_value

            if "data_management" in req.data:
                data_management_value = req.data["data_management"]
                endorsement_to_edit.data_management = data_management_value

            if "involves_animals" in req.data or "involves_plants" in req.data:
                involves_animals_value = req.data["involves_animals"]
                involves_plants_value = req.data["involves_plants"]
                aec_approval_value = req.data["ae_endorsement"]
                hc_approval_value = req.data["hc_endorsement"]

                # Auto set the endorsement to false if it does not involve plants or animals
                # Else set it to the value provided.
                if involves_animals_value == True:
                    endorsement_to_edit.ae_endorsement = aec_approval_value
                else:
                    endorsement_to_edit.ae_endorsement = False

                if involves_plants_value == True:
                    endorsement_to_edit.hc_endorsement = hc_approval_value
                else:
                    endorsement_to_edit.hc_endorsement = False

            endorsement_to_edit.save()

        project_plan = self.go(pk)
        ser = ProjectPlanSerializer(
            project_plan,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_project_plan = ser.save()
            u_project_plan.document.modifier = req.user
            u_project_plan.document.save()

            return Response(
                TinyProjectPlanSerializer(u_project_plan).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion Project Plans ====================================================================================================

# region Progress Reports ====================================================================================================


class ProgressReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_progress_reports = ProgressReport.objects.all()
        ser = TinyProgressReportSerializer(
            all_progress_reports,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = ProgressReportSerializer(
            data=req.data,
        )
        settings.LOGGER.info(msg=f"{req.user} is posting a new progress report")
        if ser.is_valid():
            progress_report = ser.save()
            return Response(
                TinyProgressReportSerializer(progress_report).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProgressReportDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProgressReport.objects.get(pk=pk)
        except ProgressReport.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        progress_report = self.go(pk)
        ser = ProgressReportSerializer(
            progress_report,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        progress_report = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting progress report {progress_report}"
        )

        progress_report.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        progress_report = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating progress report {progress_report}"
        )
        ser = ProgressReportSerializer(
            progress_report,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_progress_report = ser.save()
            u_progress_report.document.modifier = req.user
            u_progress_report.document.save()

            return Response(
                TinyProgressReportSerializer(u_progress_report).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class UpdateProgressReport(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            report = ProgressReport.objects.filter(document=pk).first()
        except ProgressReport.DoesNotExist:
            raise NotFound
        return report

    def post(self, req):
        report = self.go(pk=int(req.data["main_document_pk"]))
        section = req.data["section"]
        html_data = req.data["html"]

        ser = ProgressReportSerializer(
            report,
            data={f"{section}": html_data},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            up_ser = ProgressReportSerializer(updated)
            return Response(
                up_ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProgressReportByYear(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, project, year):
        try:
            obj = (
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
                    "report",  # AnnualReport
                    "report__creator",
                    "report__modifier",
                )
                .prefetch_related(
                    "document__project__business_area__division__directorate_email_list",
                    # Avoid N+1: Prefetch the project members so TeamMemberMixin can use them
                    "document__project__members",
                    "document__project__members__user",
                    "document__project__members__user__profile",
                    "document__project__members__user__work",
                    "document__project__members__user__work__business_area",
                    "document__project__members__user__caretaker",
                    "document__project__members__user__caretaker_for",
                )
                .get(year=year, document__project=project)
            )
        except ProgressReport.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, project, year):
        progress_report = self.go(project=project, year=year)
        ser = ProgressReportSerializer(
            progress_report,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


# endregion Progress Reports ====================================================================================================

# region Student Reports ====================================================================================================


class StudentReports(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_student_reports = StudentReport.objects.all()
        ser = TinyStudentReportSerializer(
            all_student_reports,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating new student report")
        ser = StudentReportSerializer(
            data=req.data,
        )
        if ser.is_valid():
            student_report = ser.save()
            return Response(
                TinyStudentReportSerializer(student_report).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class StudentReportDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = StudentReport.objects.get(pk=pk)
        except StudentReport.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        student_report = self.go(pk)
        ser = StudentReportSerializer(
            student_report,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        student_report = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting {student_report}")

        student_report.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        student_report = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating student report {student_report}"
        )
        ser = StudentReportSerializer(
            student_report,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_student_report = ser.save()
            u_student_report.document.modifier = req.user
            u_student_report.document.save()
            return Response(
                TinyStudentReportSerializer(u_student_report).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class StudentReportByYear(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, project, year):
        try:
            obj = StudentReport.objects.get(year=year, document__project=project)
        except StudentReport.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, project, year):
        progress_report = self.go(project=project, year=year)
        ser = StudentReportSerializer(
            progress_report,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class UpdateStudentReport(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            report = StudentReport.objects.filter(document=pk).first()
        except StudentReport.DoesNotExist:
            raise NotFound
        return report

    def post(self, req):
        report = self.go(pk=int(req.data["main_document_pk"]))
        ser = StudentReportSerializer(
            report,
            data={"progress_report": req.data["html"]},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            up_ser = StudentReportSerializer(updated)
            return Response(
                up_ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


# endregion Student Reports ====================================================================================================

# region Project Closures ====================================================================================================


class ProjectClosures(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_project_closures = ProjectClosure.objects.all()
        ser = TinyProjectClosureSerializer(
            all_project_closures,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating new project closure")
        ser = ProjectClosureSerializer(
            data=req.data,
        )
        if ser.is_valid():
            project_closure = ser.save()
            return Response(
                TinyProjectClosureSerializer(project_closure).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProjectClosureDetail(APIView):

    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectClosure.objects.get(pk=pk)
        except ProjectClosure.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        project_closure = self.go(pk)
        ser = ProjectClosureSerializer(
            project_closure,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is deleting project closure {pk}")
        project_closure = self.go(pk)
        project_closure.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        project_closure = self.go(pk)
        ser = ProjectClosureSerializer(
            project_closure,
            data=req.data,
            partial=True,
        )
        settings.LOGGER.info(
            msg=f"{req.user} is updating project closure {project_closure}"
        )
        if ser.is_valid():
            u_project_closure = ser.save()
            u_project_closure.document.modifier = req.user
            u_project_closure.document.save()
            return Response(
                TinyProjectClosureSerializer(u_project_closure).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion Project Closures ====================================================================================================

# region ENDORSEMENTS & APPROVALS ==========================================================


class Endorsements(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all_endorsements = Endorsement.objects.all()
        ser = TinyEndorsementSerializer(
            all_endorsements,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting an endorsement")
        ser = EndorsementSerializer(
            data=req.data,
        )
        if ser.is_valid():
            new_endorsement = ser.save()
            return Response(
                TinyEndorsementSerializer(new_endorsement).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class EndorsementDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Endorsement.objects.get(pk=pk)
        except Endorsement.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        endorsement = self.go(pk)
        ser = EndorsementSerializer(
            endorsement,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is updating endorsement for {pk}")
        endorsement = self.go(pk)
        ser = EndorsementSerializer(
            endorsement,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_endorsement = ser.save()
            return Response(
                TinyEndorsementSerializer(u_endorsement).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class EndorsementsPendingMyAction(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting endorsements pending action")

        is_aec = req.user.is_aec
        is_superuser = req.user.is_superuser

        documents = []
        aec_input_required = []

        q_ae = Q(ae_endorsement_required=True, ae_endorsement_provided=False) & (
            Q(ae_endorsement_required=True) if is_aec or is_superuser else Q()
        )

        # Filter endorsements based on conditions
        filtered_endorsements = Endorsement.objects.filter(
            q_ae,
            project_plan__project__status__in=Project.ACTIVE_ONLY,
        )

        for endorsement in filtered_endorsements:
            if (
                endorsement.ae_endorsement_required
                and not endorsement.ae_endorsement_provided
            ):
                documents.append(endorsement)
                aec_input_required.append(endorsement)

        all_aec = MiniEndorsementSerializer(
            aec_input_required if aec_input_required else [],
            many=True,
            context={"request": req},
        ).data

        data = {
            "aec": all_aec,
        }

        return Response(data, status=HTTP_200_OK)


class SeekEndorsement(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        project_plan = self.go(pk)
        endorsement = Endorsement.objects.filter(project_plan=project_plan).first()

        end_ser = EndorsementSerializer(
            endorsement,
            data=req.data,
            partial=True,
        )

        settings.LOGGER.info(
            msg=f"{req.user} is seeking an endorsement for project plan {project_plan} with db object {endorsement}"
        )
        if end_ser.is_valid():
            with transaction.atomic():
                updated = end_ser.save()

                # If there is a pdf file, see if once exists related to the endorsement
                pdf_file = req.FILES.get("aec_pdf_file")

                if pdf_file:
                    existing_pdf = AECEndorsementPDF.objects.filter(
                        endorsement=updated
                    ).first()
                    # If it does, update it
                    if existing_pdf:
                        existing_pdf.file = pdf_file
                        existing_pdf.save()
                        settings.LOGGER.info(msg=f"Found entry and updated PDF")
                    # If it doesnt, create it
                    else:
                        # Create a new file
                        new_instance_data = {
                            "file": pdf_file,
                            "endorsement": updated.id,
                            "creator": req.user.id,
                        }
                        new_instance_serializer = AECPDFCreateSerializer(
                            data=new_instance_data
                        )

                        if new_instance_serializer.is_valid():
                            new_pdf = new_instance_serializer.save()
                            settings.LOGGER.info(msg=f"Saved new valid pdf instance")

                        else:
                            settings.LOGGER.error(
                                msg=f"{new_instance_serializer.errors}"
                            )
                            return Response(
                                new_instance_serializer.errors, HTTP_400_BAD_REQUEST
                            )

                updated_ser_data = EndorsementSerializer(updated).data

                return Response(
                    updated_ser_data,
                    HTTP_202_ACCEPTED,
                )
        else:
            settings.LOGGER.error(
                msg=f"Endorsement serializer invalid: {end_ser.errors}"
            )

            return Response(
                end_ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class DeleteAECEndorsement(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        project_plan = self.go(pk)
        endorsement = Endorsement.objects.filter(project_plan=project_plan).first()
        settings.LOGGER.info(
            msg=f"{req.user} is deleting aec endorsement and pdf for project plan {project_plan} with db object {endorsement}"
        )

        # First update the endorsement to remove approved
        end_ser = EndorsementSerializer(
            endorsement,
            data={"ae_endorsement_provided": False},
            partial=True,
        )

        if end_ser.is_valid():
            with transaction.atomic():
                # Update
                updated = end_ser.save()
                # Next delete the pdf
                pdf_obj = AECEndorsementPDF.objects.filter(
                    endorsement=endorsement
                ).first()
                if pdf_obj:
                    pdf_obj.delete()

                updated_ser_data = EndorsementSerializer(updated).data

                return Response(
                    updated_ser_data,
                    HTTP_202_ACCEPTED,
                )
        else:
            settings.LOGGER.error(
                msg=f"Endorsement serializer invalid: {end_ser.errors}"
            )

            return Response(
                end_ser.errors,
                HTTP_400_BAD_REQUEST,
            )


# endregion =========================================================================

# region Actions ====================================================================================================


class DownloadProjectDocument(APIView):
    def go(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        document_id = req.data["document_id"]
        document = self.go(document_id)
        settings.LOGGER.info(msg=f"{req.user} is trying to download pdf for {document}")
        pdf = document.pdf
        return Response(
            data=pdf,
            status=HTTP_200_OK,
        )


class RepoenProject(APIView):
    permission_classes = [IsAuthenticated]

    def get_base_document(self, project_pk):
        obj = ProjectDocument.objects.filter(
            project=project_pk, kind="projectclosure"
        ).first()
        if obj is None:
            return None
        return obj

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is reopening project belonging to doc ({pk})"
        )

        maintainer_pk = get_current_maintainer_pk()

        with transaction.atomic():
            try:
                settings.LOGGER.info(msg=f"{req.user} is reopening project {pk}")
                project_document = self.get_base_document(pk)

                if project_document == None:
                    project = Project.objects.filter(pk=pk).first()
                    project.status = Project.StatusChoices.UPDATING
                    project.save()
                else:
                    project_document.project.status = "updating"
                    project_document.project.save()
                    project = Project.objects.filter(
                        pk=project_document.project.pk
                    ).first()
                    project_document.delete()
                print("SENDING PROJECT REOPENED EMAIL")
                # Preset info
                from_email = settings.DEFAULT_FROM_EMAIL
                templ = "./email_templates/project_reopened_email.html"

                if project:
                    html_project_title = project.title
                    plain_project_name = html_project_title

                    actioning_user = User.objects.get(pk=req.user.pk)
                    actioning_user_name = f"{actioning_user.display_first_name} {actioning_user.display_last_name}"
                    actioning_user_email = f"{actioning_user.email}"

                    # Get recipient list
                    recipients_list = []
                    # get pl as the ba lead is the actioning user
                    p_leader = ProjectMember.objects.get(
                        project=project, is_leader=True
                    )
                    pl_user = p_leader.user.pk
                    pl_user_name = f"{p_leader.user.display_first_name} {p_leader.user.display_last_name}"
                    pl_user_email = f"{p_leader.user.email}"
                    p_leader_data_obj = {
                        "pk": pl_user,
                        "name": pl_user_name,
                        "email": pl_user_email,
                    }
                    recipients_list.append(p_leader_data_obj)
                    project_tag = project.get_project_tag()
                    processed = []
                    for recipient in recipients_list:
                        if recipient["pk"] not in processed:
                            if settings.ENVIRONMENT == "production":
                                print(
                                    f"PRODUCTION: Sending email to {recipient["name"]}"
                                )
                                email_subject = f"SPMS: {project_tag} Re-Opened"
                                to_email = [recipient["email"]]

                                template_props = {
                                    "user_kind": "Project Lead",
                                    "email_subject": email_subject,
                                    "actioning_user_email": actioning_user_email,
                                    "actioning_user_name": actioning_user_name,
                                    "recipient_name": recipient["name"],
                                    "project_id": project.pk,
                                    "plain_project_name": plain_project_name,
                                    "document_type": "closure",
                                    "site_url": settings.SITE_URL,
                                    "dbca_image_path": get_encoded_image(),
                                }

                                template_content = render_to_string(
                                    templ, template_props
                                )

                                try:
                                    send_email_with_embedded_image(
                                        recipient_email=to_email,
                                        subject=email_subject,
                                        html_content=template_content,
                                    )
                                    # send_mail(
                                    #     email_subject,
                                    #     template_content,
                                    #     from_email,
                                    #     to_email,
                                    #     fail_silently=False,
                                    #     html_message=template_content,
                                    # )
                                except Exception as e:
                                    settings.LOGGER.error(
                                        msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                                    )
                                    return Response(
                                        {"error": str(e)},
                                        status=HTTP_400_BAD_REQUEST,
                                    )
                            else:
                                # test
                                print(f"TEST: Sending email to {recipient["name"]}")
                                if recipient["pk"] == maintainer_pk:
                                    email_subject = f"SPMS: {project_tag} Re-Opened"
                                    to_email = [recipient["email"]]

                                    template_props = {
                                        "user_kind": "Project Lead",
                                        "email_subject": email_subject,
                                        "actioning_user_email": actioning_user_email,
                                        "actioning_user_name": actioning_user_name,
                                        "recipient_name": recipient["name"],
                                        "project_id": project.pk,
                                        "plain_project_name": plain_project_name,
                                        "document_type": "closure",
                                        "site_url": settings.SITE_URL,
                                        "dbca_image_path": get_encoded_image(),
                                    }

                                    template_content = render_to_string(
                                        templ, template_props
                                    )

                                    try:
                                        send_email_with_embedded_image(
                                            recipient_email=to_email,
                                            subject=email_subject,
                                            html_content=template_content,
                                        )
                                        # send_mail(
                                        #     email_subject,
                                        #     template_content,
                                        #     from_email,
                                        #     to_email,
                                        #     fail_silently=False,
                                        #     html_message=template_content,
                                        # )
                                    except Exception as e:
                                        settings.LOGGER.error(
                                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                                        )
                                        return Response(
                                            {"error": str(e)},
                                            status=HTTP_400_BAD_REQUEST,
                                        )
                            processed.append(recipient["pk"])

                    return Response(
                        "Emails Sent!",
                        status=HTTP_202_ACCEPTED,
                    )
                return Response(status=HTTP_204_NO_CONTENT)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                return Response(f"{e}", status=HTTP_400_BAD_REQUEST)


class DownloadAnnualReport(APIView):
    def get(self, req):
        settings.LOGGER.error(msg=f"{req.user} is downloading annual report")
        pass


# endregion =========================================================================

# region Admin Actions ==================================================


class BatchApprove(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        settings.LOGGER.warning(
            msg=f"{req.user} is attempting to batch approve reports..."
        )
        if req.user.is_superuser == False:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        # Get the last report with the highest year
        last_report = AnnualReport.objects.order_by("-year").first()

        # Handle the case where no report is found
        if not last_report:
            return Response(
                {"error": "No annual report found!"},
                status=HTTP_404_NOT_FOUND,
            )

        relevant_docs_belonging_to_last_report_awaiting_final_approval = (
            ProjectDocument.objects.filter(
                Q(kind="studentreport") | Q(kind="progressreport"),
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=True,
            )
            .exclude(
                project__status__in=[
                    "suspended",
                    "terminated",
                    "completed",
                    "closing",
                    "closure_requested",
                ],
            )
            .select_related("project")  # Optimise project access
            .prefetch_related(
                "student_report_details",
                "progress_report_details",
            )
            .all()
        )

        try:
            for doc in relevant_docs_belonging_to_last_report_awaiting_final_approval:
                # FIRST ENSURE THEY BELONG TO THE ANNUAL REPORT BY FINDING THE YEAR ON EACH MODEL
                if doc.kind == "studentreport":
                    sr_obj = StudentReport.objects.filter(report=last_report).first()
                    if sr_obj:
                        doc.directorate_approval_granted = True
                        doc.status = "approved"
                        doc.save()
                        project = Project.objects.filter(pk=doc.project.pk).first()
                        project.status = Project.StatusChoices.ACTIVE
                        project.save()

                elif doc.kind == "progressreport":
                    pr_obj = ProgressReport.objects.filter(report=last_report).first()
                    if pr_obj:
                        doc.directorate_approval_granted = True
                        doc.status = "approved"
                        doc.save()
                        project = Project.objects.filter(pk=doc.project.pk).first()
                        project.status = Project.StatusChoices.ACTIVE
                        project.save()

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response(
                str(e),
                HTTP_400_BAD_REQUEST,
            )
        else:
            settings.LOGGER.info(
                msg=f"Reports have been batch approved for year {last_report.year}"
            )
            return Response(
                "Success",
                HTTP_202_ACCEPTED,
            )


class BatchApproveOld(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        settings.LOGGER.warning(
            msg=f"{req.user} is attempting to batch approve older reports..."
        )
        if not req.user.is_superuser:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        # Get the last report with the highest year
        last_report = AnnualReport.objects.order_by("-year").first()

        # Handle the case where no report is found
        if not last_report:
            return Response(
                {"error": "No annual reports found!"},
                status=HTTP_404_NOT_FOUND,
            )

        # Get relevant documents with optimised queries using select_related and prefetch_related
        relevant_docs = (
            ProjectDocument.objects.filter(
                Q(kind="studentreport") | Q(kind="progressreport"),
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=True,
            )
            .exclude(
                project__status__in=["suspended", "terminated", "completed"],
            )
            .select_related("project")  # Optimise project access
            .prefetch_related(
                "project__members",  # Optimise members access
                "student_report_details",  # Optimise student report access
                "progress_report_details",  # Optimise progress report access
            )
        )

        try:
            # Collect documents and projects that need updating
            docs_to_update = []
            projects_to_update = []

            for doc in relevant_docs:
                should_process = False

                if doc.kind == "studentreport":
                    # Use prefetched data instead of separate query
                    sr_obj = (
                        doc.student_report_details.first()
                        if doc.student_report_details.exists()
                        else None
                    )

                    # Fix: Use .count() instead of .length ... js habit
                    if sr_obj and doc.project.members.count() == 0:
                        continue

                    if sr_obj and sr_obj.report != last_report:
                        should_process = True

                elif doc.kind == "progressreport":
                    # Use prefetched data instead of separate query
                    pr_obj = (
                        doc.progress_report_details.first()
                        if doc.progress_report_details.exists()
                        else None
                    )

                    # using .count() instead of .length
                    if pr_obj and doc.project.members.count() == 0:
                        continue

                    if pr_obj and pr_obj.report != last_report:
                        should_process = True

                if should_process:
                    # Prepare document for bulk update
                    doc.project_lead_approval_granted = True
                    doc.business_area_lead_approval_granted = True
                    doc.directorate_approval_granted = True
                    doc.status = "approved"
                    docs_to_update.append(doc)

                    # Prepare project for bulk update (avoid duplicate projects)
                    project = doc.project
                    if project not in projects_to_update:
                        project.status = Project.StatusChoices.ACTIVE
                        projects_to_update.append(project)

            # Bulk update documents
            if docs_to_update:
                ProjectDocument.objects.bulk_update(
                    docs_to_update,
                    [
                        "project_lead_approval_granted",
                        "business_area_lead_approval_granted",
                        "directorate_approval_granted",
                        "status",
                    ],
                )

            # Bulk update projects
            if projects_to_update:
                Project.objects.bulk_update(projects_to_update, ["status"])

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response(
                str(e),
                HTTP_400_BAD_REQUEST,
            )
        else:
            settings.LOGGER.info(
                msg=f"Reports have been batch approved for annual report documents before year: {last_report.year}"
            )
            return Response(
                "Success",
                HTTP_202_ACCEPTED,
            )


# No Email
class FinalDocApproval(APIView):
    permission_classes = [IsAuthenticated]

    def get_document(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        documentPk = req.data.get("documentPk")
        isActive = req.data.get("isActive")

        if isActive == False:
            settings.LOGGER.info(
                msg=f"{req.user} is providing final approval for {documentPk}"
            )
            document = self.get_document(pk=documentPk)

            data = {
                "project_lead_approval_granted": True,
                "business_area_lead_approval_granted": True,
                "directorate_approval_granted": True,
                "modifier": req.user.pk,
                "status": "approved",
            }
            ser = ProjectDocumentSerializer(
                document,
                data=data,
                partial=True,
            )
            if ser.is_valid():
                u_document = ser.save()
                u_document.project.status = Project.StatusChoices.ACTIVE
                u_document.project.save()
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )
            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        elif isActive == True:
            settings.LOGGER.info(
                msg=f"{req.user} is recalling final approval for docID: {documentPk}"
            )
            document = self.get_document(pk=documentPk)

            data = {
                "directorate_approval_granted": False,
                "modifier": req.user.pk,
                "status": "inapproval",
            }
            ser = ProjectDocumentSerializer(
                document,
                data=data,
                partial=True,
            )
            if ser.is_valid():
                u_document = ser.save()
                u_document.project.status = Project.StatusChoices.UPDATING
                u_document.project.save()
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )
            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            print("Noned")
            return Response(
                {"error": "Something went wrong!"},
                status=HTTP_400_BAD_REQUEST,
            )


class NewCycleOpen(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        should_update = req.data["update"]
        should_prepopulate = req.data["prepopulate"]
        should_email = req.data["send_emails"]
        settings.LOGGER.warning(
            msg=f"{req.user} is attempting to batch create new progress reports for latest year {'(Including projects with status Update Requested)' if should_update else '(Active Projects Only)'}..."
        )
        if req.user.is_superuser == False:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        last_report = AnnualReport.objects.order_by("-year").first()

        # Handle the case where no report is found
        if not last_report:
            return Response(
                {"error": "No annual report found!"},
                status=HTTP_404_NOT_FOUND,
            )

        if should_update:
            eligible_projects = Project.objects.filter(
                Q(
                    kind__in=[
                        Project.CategoryKindChoices.SCIENCE,
                        Project.CategoryKindChoices.COREFUNCTION,
                        # Project.CategoryKindChoices.STUDENT,
                    ]
                )
                & Q(status__in=["active", "updating", "suspended"])
            )
        else:
            eligible_projects = Project.objects.filter(
                Q(
                    kind__in=[
                        Project.CategoryKindChoices.SCIENCE,
                        Project.CategoryKindChoices.COREFUNCTION,
                        # Project.CategoryKindChoices.STUDENT,
                    ]
                )
                & Q(status="active")
            )

        eligible_projects = eligible_projects.exclude(
            documents__progress_report_details__report__year=last_report.year
        )

        if should_update:
            eligible_student_projects = Project.objects.filter(
                Q(status__in=["active", "updating", "suspended"])
                & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
            )
        else:
            eligible_student_projects = Project.objects.filter(
                Q(status="active") & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
            )

        eligible_student_projects.exclude(
            documents__progress_report_details__report__year=last_report.year
        )

        # Combine the two querysets
        all_eligible_projects = eligible_projects | eligible_student_projects

        for project in all_eligible_projects:
            if project.kind == Project.CategoryKindChoices.STUDENT:
                typeofdoc = ProjectDocument.CategoryKindChoices.STUDENTREPORT
            elif (
                project.kind == Project.CategoryKindChoices.SCIENCE
                or project.kind == Project.CategoryKindChoices.COREFUNCTION
            ):
                typeofdoc = ProjectDocument.CategoryKindChoices.PROGRESSREPORT
            new_doc_data = {
                "old_id": 1,
                "kind": typeofdoc,
                "status": "new",
                "modifier": req.user.pk,
                "creator": req.user.pk,
                "project": project.pk,
            }

            new_project_document = ProjectDocumentCreateSerializer(data=new_doc_data)

            if new_project_document.is_valid():
                with transaction.atomic():
                    doc = new_project_document.save()
                    if project.kind != Project.CategoryKindChoices.STUDENT:

                        exists = ProgressReport.objects.filter(
                            year=last_report.year, project=project.pk
                        ).exists()

                        # Check if a progress report for the latest year somehow exists
                        if not exists:
                            if not should_prepopulate:
                                # check for previous aims and context as this doesnt usually change
                                # so prepopulate that anyway
                                try:
                                    last_one = (
                                        ProgressReport.objects.filter(
                                            project=project.pk
                                        )
                                        .order_by("-year")
                                        .first()
                                    )
                                except ProgressReport.DoesNotExist:
                                    last_one = None

                                prepopulated_aims = "<p></p>"
                                prepopulated_context = "<p></p>"
                                prepopulated_implications = "<p></p>"

                                if last_one != None:
                                    prepopulated_aims = last_one.aims
                                    prepopulated_implications = last_one.implications
                                    prepopulated_context = last_one.context

                                progress_report_data = {
                                    "document": doc.pk,
                                    "project": project.pk,
                                    "report": last_report.pk,
                                    "project": project.pk,
                                    "year": last_report.year,
                                    "context": prepopulated_context,
                                    "implications": prepopulated_implications,
                                    "future": "<p></p>",
                                    "progress": "<p></p>",
                                    "aims": prepopulated_aims,
                                }
                            else:
                                # PREPOPULATE WITH LAST YEARS DATA
                                try:
                                    last_one = (
                                        ProgressReport.objects.filter(
                                            project=project.pk
                                        )
                                        .order_by("-year")
                                        .first()
                                    )
                                except ProgressReport.DoesNotExist:
                                    last_one = None
                                if last_one != None:
                                    progress_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
                                        "project": project.pk,
                                        "year": last_report.year,
                                        "context": last_one.context,
                                        "implications": last_one.implications,
                                        "future": last_one.future,
                                        "progress": last_one.progress,
                                        "aims": last_one.aims,
                                    }
                                    # If no prior report
                                else:
                                    progress_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
                                        "project": project.pk,
                                        "year": last_report.year,
                                        "context": "<p></p>",
                                        "implications": "<p></p>",
                                        "future": "<p></p>",
                                        "progress": "<p></p>",
                                        "aims": "<p></p>",
                                    }

                            progress_report = ProgressReportCreateSerializer(
                                data=progress_report_data
                            )

                            if progress_report.is_valid():
                                progress_report.save()
                                project.status = Project.StatusChoices.UPDATING
                                project.save()
                            else:
                                settings.LOGGER.error(
                                    msg=f"Error validating progress report: {progress_report.errors}"
                                )
                                return Response(
                                    progress_report.errors, HTTP_400_BAD_REQUEST
                                )
                        else:
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                    else:
                        exists = StudentReport.objects.filter(
                            year=last_report.year, project=project.pk
                        ).exists()

                        # Check if student report somehow already exists
                        if not exists:
                            if not should_prepopulate:
                                student_report_data = {
                                    "document": doc.pk,
                                    "project": project.pk,
                                    "report": last_report.pk,
                                    "project": project.pk,
                                    "year": last_report.year,
                                    "progress_report": "<p></p>",
                                }
                            else:
                                # PREPOPULATE WITH LAST YEARS DATA
                                try:
                                    last_one = (
                                        StudentReport.objects.filter(project=project.pk)
                                        .order_by("-year")
                                        .first()
                                    )
                                except StudentReport.DoesNotExist:
                                    last_one = None
                                if last_one != None:
                                    student_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
                                        "project": project.pk,
                                        "year": last_report.year,
                                        "progress_report": last_one.progress_report,
                                    }
                                else:
                                    student_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
                                        "project": project.pk,
                                        "year": last_report.year,
                                        "progress_report": "<p></p>",
                                    }

                            student_report = StudentReportCreateSerializer(
                                data=student_report_data
                            )

                            if student_report.is_valid():
                                student_report.save()
                                project.status = Project.StatusChoices.UPDATING
                                project.save()
                            else:
                                print(student_report.errors["non_field_errors"])
                                settings.LOGGER.error(
                                    msg=f"Error validating student report {student_report.errors}"
                                )
                                return Response(
                                    student_report.errors, HTTP_400_BAD_REQUEST
                                )
                        else:
                            project.status = Project.StatusChoices.UPDATING
                            project.save()

            else:
                settings.LOGGER.error(
                    msg=f"Error opening new cycle: {new_project_document.errors}"
                )
                return Response(new_project_document.errors, HTTP_400_BAD_REQUEST)

        if should_email == True:
            print("SENDING CYCLE OPENED EMAILS")
            maintainer_pk = get_current_maintainer_pk()
            # Preset info
            from_email = settings.DEFAULT_FROM_EMAIL
            templ = "./email_templates/new_cycle_open_email.html"

            actioning_user = User.objects.get(pk=req.user.pk)
            actioning_user_name = f"{actioning_user.display_first_name} {actioning_user.display_last_name}"
            actioning_user_email = f"{actioning_user.email}"

            # Get report details:
            financial_year_string = f"{int(last_report.year-1)}-{int(last_report.year)}"
            # Get recipient list
            recipients_list = []
            bas = BusinessArea.objects.all()
            for ba in bas:
                ba_lead = ba.leader
                if ba_lead and ba_lead.is_active and ba_lead.is_staff:
                    user = ba_lead.pk
                    user_name = (
                        f"{ba_lead.display_first_name} {ba_lead.display_last_name}"
                    )
                    user_email = f"{ba_lead.email}"
                    data_obj = {"pk": user, "name": user_name, "email": user_email}
                    recipients_list.append(data_obj)

            print(recipients_list)
            processed = []
            for recipient in recipients_list:
                if recipient["pk"] not in processed:
                    if settings.ENVIRONMENT == "production":
                        print(f"PRODUCTION: Sending email to {recipient["name"]}")

                        email_subject = f"SPMS: New Reporting Cycle Open"
                        to_email = [recipient["email"]]

                        template_props = {
                            "email_subject": email_subject,
                            "actioning_user_email": actioning_user_email,
                            "actioning_user_name": actioning_user_name,
                            "financial_year_string": financial_year_string,
                            "recipient_name": recipient["name"],
                            "site_url": settings.SITE_URL,
                            "dbca_image_path": get_encoded_image(),
                        }

                        template_content = render_to_string(templ, template_props)

                        try:
                            send_email_with_embedded_image(
                                recipient_email=to_email,
                                subject=email_subject,
                                html_content=template_content,
                            )
                            # send_mail(
                            #     email_subject,
                            #     template_content,
                            #     from_email,
                            #     to_email,
                            #     fail_silently=False,
                            #     html_message=template_content,
                            # )
                        except Exception as e:
                            settings.LOGGER.error(
                                msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                            )
                            return Response(
                                {"error": str(e)},
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        # test
                        print(f"TEST: Sending email to {recipient["name"]}")
                        if recipient["pk"] == maintainer_pk:
                            email_subject = f"SPMS: New Reporting Cycle Open"
                            to_email = [recipient["email"]]

                            template_props = {
                                "email_subject": email_subject,
                                "actioning_user_email": actioning_user_email,
                                "actioning_user_name": actioning_user_name,
                                "financial_year_string": financial_year_string,
                                "recipient_name": recipient["name"],
                                "site_url": settings.SITE_URL,
                                "dbca_image_path": get_encoded_image(),
                            }

                            template_content = render_to_string(templ, template_props)

                            try:
                                send_email_with_embedded_image(
                                    recipient_email=to_email,
                                    subject=email_subject,
                                    html_content=template_content,
                                )
                                # send_mail(
                                #     email_subject,
                                #     template_content,
                                #     from_email,
                                #     to_email,
                                #     fail_silently=False,
                                #     html_message=template_content,
                                # )
                            except Exception as e:
                                settings.LOGGER.error(
                                    msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                                )
                                return Response(
                                    {"error": str(e)},
                                    status=HTTP_400_BAD_REQUEST,
                                )
                    processed.append(recipient["pk"])

            return Response(
                "Emails Sent!",
                status=HTTP_202_ACCEPTED,
            )

        return Response(
            HTTP_202_ACCEPTED,
        )


# endregion ==================================================


# region Bump Emails =======================================================


# class SendBumpEmails(APIView):
#     permission_classes = [IsAdminUser]

#     def post(self, request):
#         documents_requiring_action = request.data.get("documentsRequiringAction", [])

#         if not documents_requiring_action:
#             return Response(
#                 {"error": "No documents provided"},
#                 status=HTTP_400_BAD_REQUEST,
#             )

#         settings.LOGGER.warning(
#             msg=f"{request.user} is sending bump emails for {len(documents_requiring_action)} documents..."
#         )

#         # Email configuration
#         from_email = settings.DEFAULT_FROM_EMAIL
#         template_path = "./email_templates/bump_email.html"

#         actioning_user = User.objects.get(pk=request.user.pk)
#         actioning_user_name = (
#             f"{actioning_user.display_first_name} {actioning_user.display_last_name}"
#         )
#         actioning_user_email = actioning_user.email

#         emails_sent = 0
#         errors = []

#         for doc_data in documents_requiring_action:
#             try:
#                 # Get the user who needs to take action
#                 user_to_action = User.objects.get(pk=doc_data.get("userToTakeAction"))

#                 if (
#                     not user_to_action.is_active
#                     or not user_to_action.email
#                     or not user_to_action.is_staff
#                 ):
#                     errors.append(
#                         f"User {user_to_action.display_first_name} {user_to_action.display_last_name} is inactive, external or has no email"
#                     )
#                     continue

#                 # Get project details
#                 project = Project.objects.get(pk=doc_data.get("projectId"))

#                 # Prepare email content
#                 email_subject = (
#                     f"SPMS: Action Required - {doc_data.get('projectTitle')}"
#                 )
#                 to_email = [user_to_action.email]

#                 template_props = {
#                     "email_subject": email_subject,
#                     "actioning_user_email": actioning_user_email,
#                     "actioning_user_name": actioning_user_name,
#                     "recipient_name": f"{user_to_action.display_first_name} {user_to_action.display_last_name}",
#                     "project_title": doc_data.get("projectTitle"),
#                     "document_kind": doc_data.get("documentKind"),
#                     "action_capacity": doc_data.get("actionCapacity"),
#                     "site_url": settings.SITE_URL,
#                     "document_url": f"{settings.SITE_URL}/documents/{doc_data.get('documentId')}",
#                     "dbca_image_path": get_encoded_image(),
#                 }

#                 template_content = render_to_string(template_path, template_props)

#                 if settings.ENVIRONMENT == "production":
#                     settings.LOGGER.info(
#                         f"PRODUCTION: Sending bump email to {user_to_action.email}"
#                     )

#                     try:
#                         send_email_with_embedded_image(
#                             recipient_email=to_email,
#                             subject=email_subject,
#                             html_content=template_content,
#                         )
#                         emails_sent += 1

#                     except Exception as email_error:
#                         settings.LOGGER.error(f"Email Error: {email_error}")
#                         errors.append(
#                             f"Failed to send email to {user_to_action.email}: {str(email_error)}"
#                         )

#                 else:
#                     # In test environment, only send to maintainer
#                     maintainer_pk = get_current_maintainer_pk()
#                     if user_to_action.pk == maintainer_pk:
#                         settings.LOGGER.info(
#                             f"TEST: Sending bump email to {user_to_action.email}"
#                         )

#                         try:
#                             send_email_with_embedded_image(
#                                 recipient_email=to_email,
#                                 subject=email_subject,
#                                 html_content=template_content,
#                             )
#                             emails_sent += 1

#                         except Exception as email_error:
#                             settings.LOGGER.error(f"Email Error: {email_error}")
#                             errors.append(
#                                 f"Failed to send email to {user_to_action.email}: {str(email_error)}"
#                             )
#                     else:
#                         settings.LOGGER.info(
#                             f"TEST: Skipping email to {user_to_action.email} (not maintainer)"
#                         )

#             except User.DoesNotExist:
#                 errors.append(
#                     f"User with ID {doc_data.get('userToTakeAction')} not found"
#                 )
#             except Project.DoesNotExist:
#                 errors.append(f"Project with ID {doc_data.get('projectId')} not found")
#             except Exception as e:
#                 settings.LOGGER.error(
#                     f"Unexpected error processing document {doc_data.get('documentId')}: {str(e)}"
#                 )
#                 errors.append(
#                     f"Error processing document {doc_data.get('documentId')}: {str(e)}"
#                 )

#         # Prepare response
#         response_data = {
#             "emails_sent": emails_sent,
#             "total_documents": len(documents_requiring_action),
#         }

#         if errors:
#             response_data["errors"] = errors
#             settings.LOGGER.warning(
#                 f"Bump emails completed with {len(errors)} errors: {errors}"
#             )

#         if emails_sent > 0:
#             settings.LOGGER.info(f"Successfully sent {emails_sent} bump emails")
#             return Response(response_data, status=HTTP_200_OK)
#         else:
#             return Response(
#                 {"error": "No emails were sent", "details": errors},
#                 status=HTTP_400_BAD_REQUEST,
#             )


class SendBumpEmails(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        documents_requiring_action = request.data.get("documentsRequiringAction", [])

        if not documents_requiring_action:
            return Response(
                {"error": "No documents provided"},
                status=HTTP_400_BAD_REQUEST,
            )

        settings.LOGGER.warning(
            msg=f"{request.user} is sending bump emails for {len(documents_requiring_action)} documents..."
        )

        # Email configuration
        # from_email = settings.DEFAULT_FROM_EMAIL
        template_path = "./email_templates/bump_email.html"

        actioning_user = User.objects.get(pk=request.user.pk)
        actioning_user_name = (
            f"{actioning_user.display_first_name} {actioning_user.display_last_name}"
        )
        actioning_user_email = actioning_user.email

        # Document kind mapping to human-readable titles
        document_kind_dict = {
            "concept": "Concept Plan",
            "projectplan": "Project Plan",
            "progressreport": "Progress Report",
            "studentreport": "Student Report",
            "projectclosure": "Project Closure",
        }

        # Document kind to URL mapping
        def determine_doc_kind_url_string(kind):
            url_mapping = {
                "concept": "concept",
                "projectplan": "project",
                "progressreport": "progress",
                "studentreport": "student",
                "projectclosure": "closure",
            }
            return url_mapping.get(kind, kind)

        emails_sent = 0
        errors = []

        for doc_data in documents_requiring_action:
            try:
                # Get the user who needs to take action
                user_to_action = User.objects.get(pk=doc_data.get("userToTakeAction"))

                if (
                    not user_to_action.is_active
                    or not user_to_action.email
                    or not user_to_action.is_staff
                ):
                    errors.append(
                        f"User {user_to_action.display_first_name} {user_to_action.display_last_name} is inactive, external or has no email"
                    )
                    continue

                # Get project details
                # project = Project.objects.get(pk=doc_data.get("projectId"))

                # Get human-readable document type
                document_kind_raw = doc_data.get("documentKind")
                document_kind_title = document_kind_dict.get(
                    document_kind_raw, document_kind_raw
                )

                # Get URL-friendly document kind
                url_doc_kind = determine_doc_kind_url_string(document_kind_raw)

                # Prepare email content
                email_subject = (
                    f"SPMS: Action Required - {doc_data.get('projectTitle')}"
                )
                to_email = [user_to_action.email]

                template_props = {
                    "email_subject": email_subject,
                    "actioning_user_email": actioning_user_email,
                    "actioning_user_name": actioning_user_name,
                    "recipient_name": f"{user_to_action.display_first_name} {user_to_action.display_last_name}",
                    "recipient_email": user_to_action.email,
                    "project_title": doc_data.get("projectTitle"),
                    "project_id": doc_data.get("projectId"),
                    "document_kind": document_kind_title,  # Human-readable version
                    "document_kind_raw": document_kind_raw,  # Raw version for URL
                    "action_capacity": doc_data.get("actionCapacity"),
                    "site_url": settings.SITE_URL,
                    # Fixed document URL to go to the correct project page
                    "document_url": f"{settings.SITE_URL}/projects/{doc_data.get('projectId')}/{url_doc_kind}",
                    # "dbca_image_path": get_encoded_image(),
                }

                template_content = render_to_string(template_path, template_props)

                if settings.ENVIRONMENT == "production":
                    settings.LOGGER.info(
                        f"PRODUCTION: Sending bump email to {user_to_action.email}"
                    )

                    try:
                        send_email_with_embedded_image(
                            recipient_email=to_email,
                            subject=email_subject,
                            html_content=template_content,
                        )
                        emails_sent += 1

                    except Exception as email_error:
                        settings.LOGGER.error(f"Email Error: {email_error}")
                        errors.append(
                            f"Failed to send email to {user_to_action.email}: {str(email_error)}"
                        )

                else:
                    # In test environment, only send to maintainer
                    maintainer_pk = get_current_maintainer_pk()
                    if user_to_action.pk == maintainer_pk:
                        settings.LOGGER.info(
                            f"TEST: Sending bump email to {user_to_action.email}"
                        )

                        try:
                            send_email_with_embedded_image(
                                recipient_email=to_email,
                                subject=email_subject,
                                html_content=template_content,
                            )
                            emails_sent += 1

                        except Exception as email_error:
                            settings.LOGGER.error(f"Email Error: {email_error}")
                            errors.append(
                                f"Failed to send email to {user_to_action.email}: {str(email_error)}"
                            )
                    else:
                        settings.LOGGER.info(
                            f"TEST: Skipping email to {user_to_action.email} (not maintainer)"
                        )

            except User.DoesNotExist:
                errors.append(
                    f"User with ID {doc_data.get('userToTakeAction')} not found"
                )
            except Project.DoesNotExist:
                errors.append(f"Project with ID {doc_data.get('projectId')} not found")
            except Exception as e:
                settings.LOGGER.error(
                    f"Unexpected error processing document {doc_data.get('documentId')}: {str(e)}"
                )
                errors.append(
                    f"Error processing document {doc_data.get('documentId')}: {str(e)}"
                )

        # Prepare response
        response_data = {
            "emails_sent": emails_sent,
            "total_documents": len(documents_requiring_action),
        }

        if errors:
            response_data["errors"] = errors
            settings.LOGGER.warning(
                f"Bump emails completed with {len(errors)} errors: {errors}"
            )

        if emails_sent > 0:
            settings.LOGGER.info(f"Successfully sent {emails_sent} bump emails")
            return Response(response_data, status=HTTP_200_OK)
        else:
            return Response(
                {"error": "No emails were sent", "details": errors},
                status=HTTP_400_BAD_REQUEST,
            )


# endregion ================================================================


# region PDF GENERATION ===================================================


def determine_doc_kind_url_string(dockind: str):
    if dockind == "conceptplan" or dockind == "concept":
        return "concept"
    elif dockind == "projectplan" or dockind == "project":
        return "project"
    elif dockind == "progressreport" or dockind == "progress":
        return "progress"
    elif dockind == "studentreport" or dockind == "student":
        return "student"
    else:
        return "closure"


class UnifiedReportDocGeneration(APIView):
    permission_classes = [IsAuthenticated]

    def get_ar_media_batch(self, pk):
        """Get all AR media in a single query with minimal data"""
        media_queryset = AnnualReportMedia.objects.filter(report=pk).only(
            "kind", "file", "report_id"
        )

        return {media.kind: media for media in media_queryset}

    def get_external_projects_optimised(self, report, genkind):
        """optimised external projects with conditional filtering"""
        settings.LOGGER.info(f"Getting External Projects for {genkind} generation...")

        # Build base query
        base_query = Q(kind__in=[Project.CategoryKindChoices.EXTERNAL]) & Q(
            business_area__division__name="Biodiversity and Conservation Science"
        )

        # Add status filter for approved only
        if genkind == "approved":
            base_query &= Q(status="active")

        # Apply exclusions for both cases
        active_external_projects = (
            Project.objects.filter(base_query)
            .exclude(business_area__division__name__isnull=True)
            .exclude(
                status__in=(
                    [
                        Project.StatusChoices.COMPLETED,
                        Project.StatusChoices.SUSPENDED,
                        Project.StatusChoices.TERMINATED,
                    ]
                    if genkind == "all"
                    else []
                )  # Additional exclusions for "all"
            )
            .select_related("external_project_info")
            .prefetch_related(
                Prefetch(
                    "members",
                    queryset=ProjectMember.objects.select_related("user").filter(
                        role__in=ProjectMember.STAFF_ROLES
                    ),
                )
            )
            .only(
                "pk",
                "title",
                "external_project_info__collaboration_with",
                "external_project_info__budget",
            )
            .order_by("title")
        )

        # Manual serialization for maximum performance
        result = []
        for project in active_external_projects:
            # Get team members efficiently
            team_members = []
            if (
                hasattr(project, "_prefetched_objects_cache")
                and "members" in project._prefetched_objects_cache
            ):
                for member in project._prefetched_objects_cache["members"]:
                    if member.user.is_staff:
                        team_members.append(
                            {
                                "role": member.role,
                                "user": {
                                    "pk": member.user.pk,
                                    "display_first_name": member.user.display_first_name,
                                    "display_last_name": member.user.display_last_name,
                                    "is_staff": member.user.is_staff,
                                },
                            }
                        )

            result.append(
                {
                    "pk": project.pk,
                    "title": project.title,
                    "partners": (
                        project.external_project_info.collaboration_with
                        if hasattr(project, "external_project_info")
                        and project.external_project_info
                        else ""
                    ),
                    "funding": (
                        project.external_project_info.budget
                        if hasattr(project, "external_project_info")
                        and project.external_project_info
                        else ""
                    ),
                    "team_members": team_members,
                }
            )

        return result

    def get_reports_optimised(self, report, genkind):
        """optimised reports query with conditional approval filtering"""
        settings.LOGGER.info(
            f"Getting Student & Progress Reports for {genkind} generation"
        )

        base_filter = Q(report=report) & Q(
            project__business_area__division__name="Biodiversity and Conservation Science"
        )

        # Add approval filter for student reports only when needed
        student_filter = base_filter
        if genkind == "approved":
            student_filter &= Q(document__status="approved")

        # optimised Student Reports query
        active_sr_docs = (
            StudentReport.objects.filter(student_filter)
            .exclude(project__business_area__division__name__isnull=True)
            .select_related(
                "document",
                "project",
                "project__business_area",
                "project__image",
                "project__student_project_info",
            )
            .prefetch_related(
                Prefetch(
                    "project__members",
                    queryset=ProjectMember.objects.select_related(
                        "user", "user__profile"
                    ),
                ),
                "project__area",
                "project__business_area__image",
            )
        )

        # handle project 1127 separately
        # First get the regular progress reports
        regular_pr_docs = (
            ProgressReport.objects.filter(base_filter)
            .exclude(project__business_area__division__name__isnull=True)
            .select_related(
                "document",
                "project",
                "project__business_area",
                "project__image",
                "project__student_project_info",
            )
            .prefetch_related(
                Prefetch(
                    "project__members",
                    queryset=ProjectMember.objects.select_related(
                        "user", "user__profile"
                    ),
                ),
                "project__area",
                "project__business_area__image",
            )
        )

        # Get project 1127 reports separately (without business_area requirements)
        project_1127_pr_docs = (
            ProgressReport.objects.filter(Q(report=report) & Q(project__id=1127))
            .select_related(
                "document",
                "project",
                "project__image",
                "project__student_project_info",
            )
            .prefetch_related(
                Prefetch(
                    "project__members",
                    queryset=ProjectMember.objects.select_related(
                        "user", "user__profile"
                    ),
                ),
                "project__area",
            )
        )

        # Combine the querysets
        active_pr_docs = list(regular_pr_docs) + list(project_1127_pr_docs)

        # Optimised HTML cleaning with regex compilation
        empty_p_pattern = re.compile(r"<p>(&nbsp;|\s)*</p>")
        nbsp_pattern = re.compile(r"&nbsp;")

        def removeempty_p_optimised(html_content):
            if not html_content:
                return html_content
            html_content = empty_p_pattern.sub("", html_content)
            html_content = nbsp_pattern.sub(" ", html_content)
            return html_content

        # Process reports efficiently
        for report_obj in active_pr_docs:
            # Clean HTML fields
            report_obj.context = removeempty_p_optimised(report_obj.context)
            report_obj.aims = removeempty_p_optimised(report_obj.aims)
            report_obj.progress = removeempty_p_optimised(report_obj.progress)
            report_obj.implications = removeempty_p_optimised(report_obj.implications)
            report_obj.future = removeempty_p_optimised(report_obj.future)

        for sreport in active_sr_docs:
            sreport.progress_report = removeempty_p_optimised(sreport.progress_report)

        # Get the real Plant Science and Herbarium business area
        try:
            plant_science_ba = BusinessArea.objects.only(
                "pk", "name", "leader_id", "introduction"
            ).get(name="Plant Science and Herbarium")
            plant_science_ba_data = {
                "name": plant_science_ba.name,
                "pk": plant_science_ba.pk,
                "leader": plant_science_ba.leader_id,
                "introduction": plant_science_ba.introduction or "",
            }
        except BusinessArea.DoesNotExist:
            # Fallback to mock data
            plant_science_ba_data = {
                "name": "Plant Science and Herbarium",
                "pk": None,
                "leader": None,
                "introduction": "",
            }

        # Use optimised serializers
        sr_ser = OptimisedStudentReportAnnualReportSerializer(active_sr_docs, many=True)
        pr_ser = OptimisedProgressReportAnnualReportSerializer(
            active_pr_docs, many=True
        )

        # Fix the business area for project 1127 in the serialised data
        for report_data in pr_ser.data:
            if report_data["document"]["project"]["pk"] == 1127:
                report_data["document"]["project"][
                    "business_area"
                ] = plant_science_ba_data

        return {
            "student_reports": sr_ser.data,
            "progress_reports": pr_ser.data,
        }

    def get_business_areas_optimised(self, participating_reports):
        """optimised business area processing with caching"""
        # Use defaultdict for efficient grouping
        ba_dict = {}
        progress_reports_by_ba = defaultdict(list)

        # Single pass through progress reports
        for pr in participating_reports["progress_reports"]:
            document = pr["document"]
            project = document["project"]
            ba = project["business_area"]

            if ba:  # Check if ba exists
                ba_pk = ba["pk"]

                # Add to BA dictionary
                if ba_pk not in ba_dict:
                    ba_dict[ba_pk] = ba

                # Group progress reports by BA
                progress_reports_by_ba[ba_pk].append(pr)

        # Get user names in batch (only for leaders we actually need)
        user_pks = [ba["leader"] for ba in ba_dict.values() if ba and ba.get("leader")]
        users_dict = {}
        if user_pks:
            users_dict = {
                user.pk: f"{user.display_first_name} {user.display_last_name}"
                for user in User.objects.filter(pk__in=user_pks).only(
                    "pk", "display_first_name", "display_last_name"
                )
            }

        # Compile regex once for text extraction
        html_tag_pattern = re.compile(r"<[^>]+>")

        def get_distilled_title_optimised(html_string):
            """Optimised text extraction"""
            if not html_string:
                return ""
            # Remove HTML tags and clean up whitespace
            clean_text = html_tag_pattern.sub(" ", html_string)
            return " ".join(clean_text.split()).strip()

        # Build sorted BA data efficiently
        sorted_ba_data = []
        for ba_pk, ba in ba_dict.items():
            progress_reports = progress_reports_by_ba[ba_pk]

            # Sort progress reports efficiently
            sorted_progress_reports = sorted(
                progress_reports,
                key=lambda x: (
                    -int(x["document"]["project"]["year"]),
                    get_distilled_title_optimised(
                        x["document"]["project"]["title"]
                    ).lower(),
                ),
            )

            ba_object = {
                "ba_name": ba["name"],
                "ba_image": ba.get("image", ""),
                "ba_leader": users_dict.get(ba.get("leader"), ""),
                "ba_introduction": ba.get("introduction", ""),
                "progress_reports": sorted_progress_reports,
            }
            sorted_ba_data.append(ba_object)

        # Sort by BA name
        return sorted(sorted_ba_data, key=lambda x: x["ba_name"])

    @transaction.atomic
    def post(self, req, pk):
        """Unified optimised POST method with genkind parameter"""
        total_start_time = time.time()

        # Get genkind from request data
        genkind = req.data.get("genkind", "all")  # Default to 'all' if not specified

        # Validate genkind parameter
        if genkind not in ["all", "approved"]:
            return Response(
                {"error": "Invalid genkind parameter. Must be 'all' or 'approved'"},
                HTTP_400_BAD_REQUEST,
            )

        settings.LOGGER.info(
            f"{req.user} is generating a {genkind} pdf for report with id {pk}"
        )

        def set_report_generation_status(report, is_generating: bool):
            AnnualReport.objects.filter(pk=report.pk).update(
                pdf_generation_in_progress=is_generating
            )

        # Fetch report with minimal data
        try:
            report = AnnualReport.objects.only(
                "pk",
                "year",
                "pdf_generation_in_progress",
                "dm",
                "dm_sign",
                "service_delivery_intro",
                "publications",
            ).get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound

        # Return if already generating
        if report.pdf_generation_in_progress:
            return Response(
                {"error": "PDF Generation already in progress"},
                HTTP_400_BAD_REQUEST,
            )

        set_report_generation_status(report=report, is_generating=True)

        try:
            # Phase 1: Media fetching
            media_start = time.time()
            media_dict = self.get_ar_media_batch(pk=report.pk)
            print(f"\n\n{media_dict}\n\n")
            media_time = time.time() - media_start
            settings.LOGGER.info(f"Media fetching: {media_time:.3f}s")

            # Helper function to get media URL
            def get_media_url(kind, default=""):
                media = media_dict.get(kind)
                return media.file.url if media else default

            # Helper function to get media file path (for Prince XML)
            def get_media_file_path(kind, default=""):
                media = media_dict.get(kind)
                if media and media.file:
                    # Construct the full file path
                    return os.path.join(base_dir, media.file.url.lstrip("/"))
                return default

            # Set up paths efficiently
            base_dir = settings.BASE_DIR
            generic_chapter_image = os.path.join(
                base_dir, "documents", "generic_chapter_image.jpg"
            )
            if not os.path.exists(generic_chapter_image):
                generic_chapter_image = ""

            # Service delivery structure data
            sds_data = {
                "intro": report.service_delivery_intro,
                "chart": get_media_url("sdchart"),
                "chapter_image": get_media_url(
                    "service_delivery", generic_chapter_image
                ),
            }

            # Get chapter images efficiently
            chapter_images = {
                "cover_chapter_image": get_media_url("cover", generic_chapter_image),
                "rear_cover_chapter_image": get_media_url(
                    "rear_cover", generic_chapter_image
                ),
                "research_chapter_image": get_media_url(
                    "research", generic_chapter_image
                ),
                "partnerships_chapter_image": get_media_url(
                    "partnerships", generic_chapter_image
                ),
                "collaborations_chapter_image": get_media_url(
                    "collaborations", generic_chapter_image
                ),
                "student_projects_chapter_image": get_media_url(
                    "student_projects", generic_chapter_image
                ),
                "publications_chapter_image": get_media_url(
                    "publications", generic_chapter_image
                ),
            }

            # Phase 2: Data fetching
            data_fetch_start = time.time()

            # Use optimised methods with genkind parameter
            participating_external_projects = self.get_external_projects_optimised(
                report=report, genkind=genkind
            )
            participating_reports = self.get_reports_optimised(
                report=report, genkind=genkind
            )
            sorted_ba_data = self.get_business_areas_optimised(participating_reports)

            data_fetch_time = time.time() - data_fetch_start
            settings.LOGGER.info(f"Data fetching: {data_fetch_time:.3f}s")

            # Phase 3: Sorting optimization
            sorting_start = time.time()

            # Compile regex once for all title processing
            html_tag_pattern = re.compile(r"<[^>]+>")

            def get_distilled_title_cached(html_string):
                if not html_string:
                    return ""
                clean_text = html_tag_pattern.sub(" ", html_string)
                return " ".join(clean_text.split()).strip()

            # Sort external projects efficiently
            sorted_external_project_data = sorted(
                participating_external_projects,
                key=lambda x: get_distilled_title_cached(x["title"]).lower(),
            )

            # Sort student reports efficiently
            sorted_srs = sorted(
                participating_reports["student_reports"],
                key=lambda x: (
                    -int(x["document"]["project"]["year"]),
                    get_distilled_title_cached(
                        x["document"]["project"]["title"]
                    ).lower(),
                ),
            )

            sorting_time = time.time() - sorting_start
            settings.LOGGER.info(f"Sorting: {sorting_time:.3f}s")

            # Phase 4: Template rendering
            render_start = time.time()

            # CSS and image paths
            rte_css_path = os.path.join(base_dir, "documents", "rte_styles.css")
            prince_css_path = os.path.join(
                base_dir, "documents", "prince_ar_document_styles.css"
            )
            dbca_image_path = f"{base_dir}/staticfiles/images/BCSTransparent.png"
            no_image_path = f"{base_dir}/staticfiles/images/image_not_available.png"

            # Optimised datetime formatting
            now = datetime.datetime.now()
            day_suffix = (
                "th"
                if 10 <= now.day % 100 <= 20
                else {1: "st", 2: "nd", 3: "rd"}.get(now.day % 10, "th")
            )
            formatted_datetime = now.strftime(f"{now.day}{day_suffix} %B, %Y @ %I:%M%p")

            # DBCA banners

            # For the main cover image (used in template as dbca_image_path)
            dbca_banner = media_dict.get("dbca_banner")
            dbca_banner_cropped = media_dict.get("dbca_banner_cropped")

            dbca_image_path = ""
            if dbca_banner and dbca_banner.file:
                dbca_image_path = os.path.join(
                    base_dir, dbca_banner.file.url.lstrip("/")
                )

            # For the cropped banner used in headers
            dbca_banner_cropped_path = ""
            if dbca_banner_cropped and dbca_banner_cropped.file:
                dbca_banner_cropped_path = os.path.join(
                    base_dir, dbca_banner_cropped.file.url.lstrip("/")
                )
            print(f"DBCA: {dbca_banner}\n")
            print(f"DBCA IMAGE Path: {dbca_image_path}\n")
            print(f"DBCA Crop: {dbca_banner_cropped}\n")
            print(f"DBCA Crop IMAGE Path: {dbca_banner_cropped_path}\n")

            # Template context preparation
            template_context = {
                "time_generated": formatted_datetime,
                "prince_css_path": prince_css_path,
                "dbca_image_path": dbca_image_path,
                "dbca_cropped_image_path": dbca_banner_cropped_path,
                "no_image_path": no_image_path,
                "server_url": (
                    "http://127.0.0.1:8000"
                    if settings.DEBUG
                    else settings.PRINCE_SERVER_URL
                ),
                "frontend_url": (
                    "http://127.0.0.1:3000" if settings.DEBUG else settings.SITE_URL
                ),
                "base_url": base_dir,
                "financial_year_string": f"{int(report.year-1)}-{int(report.year)}",
                "directors_message_data": report.dm,
                "directors_message_sign_off": report.dm_sign,
                "sds_data": sds_data,
                "sorted_ba_data_and_pr_dict": sorted_ba_data,
                "sorted_external_project_data": sorted_external_project_data,
                "sorted_student_report_array": sorted_srs,
                "publications_data": report.publications,
                "population_time": f"{float(time.time() - total_start_time):.3f}",
                "generic_chapter_image_path": generic_chapter_image,
                **chapter_images,
            }

            # Render template
            html_content = get_template("annual_report.html").render(template_context)

            render_time = time.time() - render_start
            settings.LOGGER.info(f"Template rendering: {render_time:.3f}s")

            # Phase 5: PDF generation
            pdf_start = time.time()

            temp_dir = tempfile.gettempdir()
            html_file_path = os.path.join(
                temp_dir, f"_Annual_Report_{genkind}_{report.pk}.html"
            )

            with open(html_file_path, "w", encoding="utf-8") as html_file:
                html_file.write(html_content)

            all_css_paths = ",".join([rte_css_path, prince_css_path])

            p = subprocess.Popen(
                ["prince", "-", f"--style={all_css_paths}", "--javascript"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            outs, errs = p.communicate(html_content.encode("utf-8"))

            if p.returncode:
                settings.LOGGER.error(f"Prince XML error: {errs}")
                set_report_generation_status(report=report, is_generating=False)
                return Response({"error": True}, status=HTTP_400_BAD_REQUEST)

            pdf = outs
            pdf_filename = f"_Annual_Report_{genkind}_{report.pk}.pdf"
            file_content = ContentFile(pdf, name=pdf_filename)

            pdf_time = time.time() - pdf_start
            settings.LOGGER.info(f"PDF generation: {pdf_time:.3f}s")

            # Phase 6: Save PDF
            save_start = time.time()

            doc_pdf, created = AnnualReportPDF.objects.get_or_create(
                report=report, defaults={"file": file_content, "creator": req.user}
            )

            if not created:
                # Update existing
                if doc_pdf.file:
                    default_storage.delete(doc_pdf.file.path)
                doc_pdf.file = file_content
                doc_pdf.save()

            # Clean up temp file
            try:
                os.remove(html_file_path)
            except:
                pass

            save_time = time.time() - save_start
            settings.LOGGER.info(f"PDF saving: {save_time:.3f}s")

            set_report_generation_status(report, False)

            total_time = time.time() - total_start_time
            megabytes_size = len(pdf) / (1024**2)

            settings.LOGGER.info(
                f"\n==============Performance breakdown==============\nMedia: {media_time:.3f}s,\nFetch Data: {data_fetch_time:.3f}s,\nSort: {sorting_time:.3f}s,\nRender Template: {render_time:.3f}s,\nPDF Gen: {pdf_time:.3f}s,\nSave: {save_time:.3f}s"
            )
            settings.LOGGER.info(f"TOTAL TIME ({genkind}): {total_time:.3f}s")
            settings.LOGGER.info(f"PDF size: {megabytes_size:.2f} MB")

            return Response(
                AnnualReportPDFSerializer(doc_pdf).data,
                status=HTTP_201_CREATED if created else HTTP_202_ACCEPTED,
            )

        except Exception as e:
            settings.LOGGER.error(f"Error generating {genkind} report: {e}")
            set_report_generation_status(report=report, is_generating=False)
            return Response({"error": True}, status=HTTP_400_BAD_REQUEST)


class CancelReportDocGeneration(APIView):
    permission_classes = [IsAuthenticated]

    def get_main_doc(self, pk):
        # Gets the primary document that the concept plan belongs to
        try:
            doc = AnnualReport.objects.filter(pk=pk).first()
        except AnnualReport.DoesNotExist:
            raise NotFound
        return doc

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is canceling PDF GEN for Annual Report {pk}"
        )
        doc = self.get_main_doc(pk=pk)
        # doc.pdf_generation_in_progress = False
        # updated = doc.save()

        ser = AnnualReportSerializer(
            doc,
            data={"pdf_generation_in_progress": False},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            ser = AnnualReportSerializer(updated)
            settings.LOGGER.info(msg=f"Cancel Success")
            return Response(
                ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            print(ser.errors)
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class BeginProjectDocGeneration(APIView):
    permission_classes = [IsAuthenticated]

    def get_main_doc(self, pk):
        # Gets the primary document that the concept plan belongs to
        try:
            doc = ProjectDocument.objects.filter(pk=pk).first()
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return doc

    def get_concept_plan(self, pk):
        # Gets the actual concept plan, with all the html data
        try:
            cp = ConceptPlan.objects.filter(document=pk).first()
        except ConceptPlan.DoesNotExist:
            raise NotFound
        return cp

    def get_project_plan(self, pk):
        # Gets the actual project plan, with all the html data
        try:
            pp = ProjectPlan.objects.filter(document=pk).first()
        except ProjectPlan.DoesNotExist:
            raise NotFound
        return pp

    def get_project_closure(self, pk):
        # Gets the actual project closure, with all the html data
        try:
            pc = ProjectClosure.objects.filter(document=pk).first()
        except ProjectClosure.DoesNotExist:
            raise NotFound
        return pc

    def get_progress_report(self, pk):
        # Gets the actual progress report, with all the html data
        try:
            pr = ProgressReport.objects.filter(document=pk).first()
        except ProgressReport.DoesNotExist:
            raise NotFound
        return pr

    def get_student_report(self, pk):
        # Gets the actual student report, with all the html data
        try:
            sr = StudentReport.objects.filter(document=pk).first()
        except StudentReport.DoesNotExist:
            raise NotFound
        return sr

    def post(self, req, pk):
        doc = self.get_main_doc(pk=pk)
        settings.LOGGER.info(
            msg=f"{req.user} is generating Project Doc PDF for document {doc}"
        )
        document_type = doc.kind

        # General Helper Funcs
        def apply_title_styling_to_project_title(title):
            # Parse the HTML content
            soup = BeautifulSoup(title, "html.parser")

            # Create a new h1 tag
            h1_tag = soup.new_tag("h1")

            # Apply the specified styles to h1 tag
            h1_tag[
                "style"
            ] = """
                color: rgb(0, 102, 204);
                font-size: 24px; 
                font-weight: 400; 
                text-align: center; 
                padding: 0px; 
                margin-top: 2.5rem; 
                margin-bottom: 30px; 
                margin-left: 0px; 
                margin-right: 0px;
                cursor: pointer;
            """

            # Iterate through all b tags inside the p tag and set their style
            for strong_tag in soup.p.find_all("strong"):
                strong_tag[
                    "style"
                ] = """
                    color: rgb(0, 102, 204);
                """

            # Transfer content from p tag to h1 tag
            h1_tag.extend(soup.p.contents)

            # Replace the original p tag with the new h1 tag
            soup.p.replace_with(h1_tag)

            # Return the modified HTML as a string
            return str(soup)

        def get_project_team(project_pk):
            # Get the member objects
            members = ProjectMember.objects.filter(project=project_pk).all()

            # Separate leader and other members
            leader = None
            other_members = []

            for member in members:
                if member.is_leader:
                    leader = member
                else:
                    other_members.append(member)

            # Sort other members based on their position value
            sorted_members = sorted(other_members, key=attrgetter("position"))

            # Create team_name_array with leader at the beginning and then other members
            team_name_array = []
            if leader:
                team_name_array.append(
                    f"{leader.user.display_first_name} {leader.user.display_last_name}"
                )

            for member in sorted_members:
                team_name_array.append(
                    f"{member.user.display_first_name} {member.user.display_last_name}"
                )

            return team_name_array

        def get_project_image(project_pk):
            try:
                image = ProjectPhoto.objects.get(project=project_pk)
            except ProjectPhoto.DoesNotExist:
                return None
            return image

        def get_methodology_image(project_pk):
            try:
                image = ProjectPlanMethodologyPhoto.objects.get(
                    project_plan__project=project_pk
                )
            except ProjectPlanMethodologyPhoto.DoesNotExist:
                return None
            return image

        def extract_html_table_data(html_data):
            # Extract relevant information from HTML table data and convert it to a list of lists using BeautifulSoup
            soup = BeautifulSoup(html_data, "html.parser")

            table_data = []
            for row in soup.find_all("tr"):
                row_data = [cell.text.strip() for cell in row.find_all(["th", "td"])]
                table_data.append(row_data)

            return table_data

        def iterate_rows_in_json_table(data_as_list):

            table_innards = []

            for row_index, row in enumerate(data_as_list):
                row_contents = "".join(
                    [
                        f"<{'th' if (row_index == 0 or col_index == 0) else 'td'} "
                        + f"class='table-cell-light{' table-cell-header-light' if row_index == 0 or col_index == 0 else ''}'>"
                        + f"{col}"
                        + f"</{'th' if (row_index == 0 or col_index == 0) else 'td'}>"
                        for col_index, col in enumerate(row)
                    ]
                )
                row_data = f"<tr>{row_contents}</tr>"
                table_innards.append(row_data)

            return_table = f'<table class="table-light">\
                <colgroup>\
                    {" ".join("<col>" for _ in range(len(data_as_list[0])))}\
                </colgroup>\
                <tbody>{"".join(table_innards)}</tbody>\
            </table>'
            return return_table

        def generate_html_table_from_json_data(table_data):
            if (
                isinstance(table_data, str)
                and table_data.startswith("[[")
                and table_data.endswith("]]")
            ):
                # Convert the string to a list using ast.literal_eval (safer than eval)
                try:
                    table_data = ast.literal_eval(table_data)
                except (ValueError, SyntaxError):
                    return table_data  # If it's not valid, return as-is
            elif (
                isinstance(table_data, str)
                and table_data.startswith("<table")
                and table_data.endswith("</table>")
            ):
                # If HTML data received, extract relevant information
                table_data = extract_html_table_data(table_data)
            elif isinstance(table_data, str):
                # If a string contains a table but doesn't both start and end with <table> tags, try to extract relevant information
                extracted_table_data = extract_html_table_data(table_data)
                if extracted_table_data:
                    table_data = extracted_table_data
                else:
                    # No table found in the HTML, return the original content as-is
                    return table_data
            elif not all(isinstance(row, list) for row in table_data):
                # If neither JSON-like nor HTML-like data is received, raise an error
                raise ValueError(
                    f"Input must be a list of lists or a valid string representation of a list of lists or HTML table.\nProvided Input: {table_data}"
                )

            # Safer final conversion
            try:
                html = iterate_rows_in_json_table(ast.literal_eval(f"{table_data}"))
            except (ValueError, SyntaxError):
                html = iterate_rows_in_json_table(table_data)  # Trying without eval

            return html

        def replace_table_in_html_string(html_data):

            # Avoid syntax errors within LInux due to nested f string
            def gen_html_table_from_list_structure(table_data):
                table_rows = "".join(
                    [
                        "<tr>{}</tr>".format(
                            "".join(
                                [
                                    "<{} {}>{}</{}>".format(
                                        (
                                            "th"
                                            if (row_index == 0 or col_index == 0)
                                            else "td"
                                        ),
                                        f"class='table-cell-light{' table-cell-header-light' if row_index == 0 or col_index == 0 else ''}'",
                                        col,
                                        (
                                            "th"
                                            if (row_index == 0 or col_index == 0)
                                            else "td"
                                        ),
                                    )
                                    for col_index, col in enumerate(row)
                                ]
                            )
                        )
                        for row_index, row in enumerate(table_data)
                    ]
                )

                # Complete the HTML table
                replaced_data = f'<table class="table-light">\
                    <colgroup>\
                        {" ".join("<col>" for _ in range(len(table_data[0])))}\
                    </colgroup>\
                    <tbody>{table_rows}</tbody>\
                </table>'

                return replaced_data

            if html_data is None:
                return "<p></p>"
            if (
                isinstance(html_data, str)
                and html_data.startswith("[[")
                and html_data.endswith("]]")
            ):
                # Convert the string to a list using eval and pass to the function
                html_data = iterate_rows_in_json_table(eval(html_data))
                return html_data
            elif isinstance(html_data, str):
                soup = BeautifulSoup(html_data, "html.parser")

                for table_tag in soup.find_all("table"):
                    table_data = extract_html_table_data(str(table_tag))
                    if table_data:
                        new_table = gen_html_table_from_list_structure(table_data)
                        table_tag.replace_with(BeautifulSoup(new_table, "html.parser"))

                # print("SOUP:", soup)
                return str(soup)

        def replace_dark_with_light_style(html_string):
            if html_string != None:
                # Replace 'dark' with 'light' in class attributes
                modified_html = re.sub(
                    r'class\s*=\s*["\']([^"\']*dark[^"\']*)["\']',
                    lambda match: f'class="{match.group(1).replace("dark", "light")}"',
                    html_string,
                    flags=re.IGNORECASE,
                )

                # Add margin-left: 36px; to all <li> elements
                final_html = re.sub(
                    r"<li", r'<li style="margin-left: 36px;"', modified_html
                )

                return final_html
            else:
                return html_string

        def apply_styling(html_string):
            html_string = replace_dark_with_light_style(html_string=html_string)
            html_string = replace_table_in_html_string(html_string)
            return html_string

        def get_formatted_datetime(now):
            # Format the date and time
            day_with_suffix = "{}".format(now.day) + (
                "th"
                if 10 <= now.day % 100 <= 20
                else {1: "st", 2: "nd", 3: "rd"}.get(now.day % 10, "th")
            )

            formatted_datetime = now.strftime(f"{day_with_suffix} %B, %Y @ %I:%M%p")

            return formatted_datetime

        # Doc Data Get Funcs
        def return_proj_type_tag(document):
            kind = document.project.kind
            kind_dict = {
                "science": ["science", "SP"],
                "student": ["student", "STP"],
                "external": ["external", "EXT"],
                "core_function": ["core_function", "CF"],
            }

            return kind_dict[kind]

        def return_document_type_url(document, data_document=None):
            kind = document.kind
            if data_document:
                doc_year = data_document.year
                kind_dict = {
                    "concept": [
                        "concept",
                        "Science Concept Plan",
                        f"{int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "projectplan": [
                        "project",
                        "Science Project Plan",
                        f"{int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "progressreport": [
                        "progress",
                        "Progress Report",
                        f"{int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "studentreport": [
                        "student",
                        "Student Report",
                        f"{int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "projectclosure": [
                        "closure",
                        "Project Closure",
                        f"{int(doc_year-1)}-{int(doc_year)}",
                    ],
                }
            else:
                kind_dict = {
                    "concept": ["concept", "Science Concept Plan"],
                    "projectplan": ["project", "Science Project Plan"],
                    "progressreport": ["progress", "Progress Report"],
                    "studentreport": ["student", "Student Report"],
                    "projectclosure": ["closure", "Project Closure"],
                }

            return kind_dict[kind]

        def get_associated_service(pk):
            details = ProjectDetail.objects.get(project=pk)
            service = details.service
            return service

        # Concept Plan
        def get_concept_plan_data():
            print("Gettin CP DATA")
            concept_plan_data = self.get_concept_plan(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=concept_plan_data.document
            )
            doc_kind_url, doc_kind_str = return_document_type_url(
                document=concept_plan_data.document
            )

            document_tag = f"{project_kind_tag}-{concept_plan_data.project.year}-{concept_plan_data.project.number}"
            project_title = apply_title_styling_to_project_title(
                concept_plan_data.project.title
            )
            project_status = concept_plan_data.project.status
            business_area_name = concept_plan_data.project.business_area.name

            service = get_associated_service(pk=concept_plan_data.project.pk)
            if service:
                departmental_service_name = service.name
            else:
                departmental_service_name = "No Dept. Service"

            project_team = get_project_team(concept_plan_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(concept_plan_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                concept_plan_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                concept_plan_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                concept_plan_data.document.directorate_approval_granted
            )

            background = concept_plan_data.background
            aims = concept_plan_data.aims
            expected_outcomes = concept_plan_data.outcome
            collaborations = concept_plan_data.collaborations
            strategic_context = concept_plan_data.strategic_context
            staff_time_allocation = concept_plan_data.staff_time_allocation
            indicative_operating_budget = concept_plan_data.budget

            data_document_pk = concept_plan_data.pk
            main_document_pk = concept_plan_data.document.pk
            project_pk = concept_plan_data.project.pk

            return {
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "departmental_service_name": departmental_service_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "background": background,
                "aims": aims,
                "expected_outcomes": expected_outcomes,
                "collaborations": collaborations,
                "strategic_context": strategic_context,
                "staff_time_allocation": staff_time_allocation,
                "indicative_operating_budget": indicative_operating_budget,
            }

        # Project Plan
        def get_project_plan_data():
            project_plan_data = self.get_project_plan(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=project_plan_data.document
            )
            doc_kind_url, doc_kind_str = return_document_type_url(
                document=project_plan_data.document
            )

            document_tag = f"{project_kind_tag}-{project_plan_data.project.year}-{project_plan_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                project_plan_data.project.title
            )
            project_status = project_plan_data.project.status
            business_area_name = project_plan_data.project.business_area.name
            service = get_associated_service(pk=project_plan_data.project.pk)
            if service:
                departmental_service_name = service.name
            else:
                departmental_service_name = "No Dept. Service"

            project_team = get_project_team(project_plan_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(project_plan_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            methodology_image_data = TinyMethodologyImageSerializer(
                get_methodology_image(project_plan_data.project.pk)
            ).data

            if "file" in methodology_image_data:
                methodology_image = methodology_image_data["file"]
            else:
                methodology_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                project_plan_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                project_plan_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                project_plan_data.document.directorate_approval_granted
            )

            background = project_plan_data.background
            aims = project_plan_data.aims
            expected_outcomes = project_plan_data.outcome

            knowledge_transfer = project_plan_data.knowledge_transfer
            project_tasks = project_plan_data.project_tasks
            listed_references = project_plan_data.listed_references
            methodology = project_plan_data.methodology
            consolidated_funds = project_plan_data.operating_budget
            external_funds = project_plan_data.operating_budget_external
            related_projects = project_plan_data.related_projects

            # Get the endorsement specific items
            endorsements = Endorsement.objects.filter(
                project_plan=project_plan_data.pk
            ).first()
            specimens = endorsements.no_specimens
            data_management = endorsements.data_management

            data_document_pk = project_plan_data.pk
            main_document_pk = project_plan_data.document.pk
            project_pk = project_plan_data.project.pk

            return {
                "departmental_service_name": departmental_service_name,
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "methodology_image": methodology_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "background": background,
                "aims": aims,
                "expected_outcomes": expected_outcomes,
                "knowledge_transfer": knowledge_transfer,
                "project_tasks": project_tasks,
                "listed_references": listed_references,
                "methodology": methodology,
                "specimens": specimens,
                "data_management": data_management,
                "external_funds": external_funds,
                "consolidated_funds": consolidated_funds,
                "related_projects": related_projects,
            }

        # Progress Report
        def get_progress_report_data():
            progress_report_data = self.get_progress_report(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=progress_report_data.document
            )
            doc_kind_url, doc_kind_str, financial_year_string = (
                return_document_type_url(
                    document=progress_report_data.document,
                    data_document=progress_report_data,
                )
            )
            document_tag = f"{project_kind_tag}-{progress_report_data.project.year}-{progress_report_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                progress_report_data.project.title
            )
            project_status = progress_report_data.project.status
            business_area_name = progress_report_data.project.business_area.name

            project_team = get_project_team(progress_report_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(progress_report_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                progress_report_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                progress_report_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                progress_report_data.document.directorate_approval_granted
            )

            context = progress_report_data.context
            aims = progress_report_data.aims
            progress = progress_report_data.progress
            implications = progress_report_data.implications
            future = progress_report_data.future

            data_document_pk = progress_report_data.pk
            main_document_pk = progress_report_data.document.pk
            project_pk = progress_report_data.project.pk

            service = get_associated_service(pk=project_pk)
            if service:
                departmental_service_name = service.name
            else:
                departmental_service_name = "No Dept. Service"

            return {
                "departmental_service_name": departmental_service_name,
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "financial_year_string": financial_year_string,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "context": context,
                "aims": aims,
                "progress": progress,
                "implications": implications,
                "future": future,
            }

        # Student Report
        def get_student_report_data():
            # doc pk is used (document=pk)
            student_report_data = self.get_student_report(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=student_report_data.document
            )
            doc_kind_url, doc_kind_str, financial_year_string = (
                return_document_type_url(
                    document=student_report_data.document,
                    data_document=student_report_data,
                )
            )
            document_tag = f"{project_kind_tag}-{student_report_data.project.year}-{student_report_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                student_report_data.project.title
            )
            project_status = student_report_data.project.status
            business_area_name = student_report_data.project.business_area.name

            project_id = student_report_data.document.project_id
            service = get_associated_service(pk=project_id)

            if service:
                departmental_service_name = service.name
            else:
                departmental_service_name = "No Dept. Service"

            project_team = get_project_team(student_report_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(student_report_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                student_report_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                student_report_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                student_report_data.document.directorate_approval_granted
            )

            progress_report = student_report_data.progress_report

            data_document_pk = student_report_data.pk
            main_document_pk = student_report_data.document.pk
            project_pk = student_report_data.project.pk

            return {
                "departmental_service_name": departmental_service_name,
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "financial_year_string": financial_year_string,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "progress_report": progress_report,
            }

        # Project Closure
        def get_project_closure_data():
            project_closure_data = self.get_project_closure(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=project_closure_data.document
            )
            doc_kind_url, doc_kind_str = return_document_type_url(
                document=project_closure_data.document
            )

            document_tag = f"{project_kind_tag}-{project_closure_data.project.year}-{project_closure_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                project_closure_data.project.title
            )
            project_status = project_closure_data.project.status
            business_area_name = project_closure_data.project.business_area.name

            project_team = get_project_team(project_closure_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(project_closure_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                project_closure_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                project_closure_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                project_closure_data.document.directorate_approval_granted
            )

            reason = project_closure_data.reason
            knowledge_transfer = project_closure_data.knowledge_transfer
            data_location = project_closure_data.data_location
            hardcopy_location = project_closure_data.hardcopy_location
            backup_location = project_closure_data.backup_location
            scientific_outputs = project_closure_data.scientific_outputs
            intended_outcome = project_closure_data.intended_outcome

            data_document_pk = project_closure_data.pk
            main_document_pk = project_closure_data.document.pk
            project_pk = project_closure_data.project.pk

            service = get_associated_service(pk=project_pk)
            if service:
                departmental_service_name = service.name
            else:
                departmental_service_name = "No Dept. Service"

            return {
                "departmental_service_name": departmental_service_name,
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "reason": reason,
                "knowledge_transfer": knowledge_transfer,
                "data_location": data_location,
                "hardcopy_location": hardcopy_location,
                "backup_location": backup_location,
                "scientific_outputs": scientific_outputs,
                "intended_outcome": intended_outcome,
            }

        # Doc Wide Variables
        rte_css_path = os.path.join(settings.BASE_DIR, "documents", "rte_styles.css")
        fonts_folder_path = os.path.join(
            settings.BASE_DIR, "documents", "static", "fonts"
        )
        prince_css_path = os.path.join(
            settings.BASE_DIR, "documents", "prince_project_document_styles.css"
        )
        # dbca_image_path = get_encoded_ar_dbca_image()

        # dbca_image_path = os.path.join(
        #     settings.BASE_DIR, "documents", "BCSTransparent.png"
        # )
        dbca_image_path = f"{settings.BASE_DIR}/staticfiles/images/BCSTransparent.png"

        # dbca_cropped_image_path = os.path.join(
        #     settings.BASE_DIR, "documents", "BCSTransparentCropped.png"
        # )
        dbca_cropped_image_path = (
            f"{settings.BASE_DIR}/staticfiles/images/BCSTransparentCropped.png"
        )

        # no_image_path = os.path.join(
        #     settings.BASE_DIR, "documents", "image_not_available.png"
        # )
        no_image_path = (
            f"{settings.BASE_DIR}/staticfiles/images/image_not_available.png"
        )

        # Get innerhtml of element
        def get_inner_html(html_content, html_tag):
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Find the element by its tag
            element = soup.find(html_tag)

            # Check if the element is found
            if element:
                # Get the inner HTML of the element
                inner_html = str(element.decode_contents())

                return inner_html
            else:
                return None

        # Begin
        doc.pdf_generation_in_progress = True
        doc.save()

        if document_type == "concept":
            doc_data = get_concept_plan_data()
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    # Styles & url
                    "fonts_folder_path": fonts_folder_path,
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "departmental_service_name": doc_data["departmental_service_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "background": {
                            "title": "Background",
                            "data": apply_styling(doc_data["background"]),
                        },
                        "aims": {
                            "title": "Aims",
                            "data": apply_styling(doc_data["aims"]),
                        },
                        "outcomes": {
                            "title": "Expected Outcomes",
                            "data": apply_styling(doc_data["expected_outcomes"]),
                        },
                        "context": {
                            "title": "Strategic Context",
                            "data": apply_styling(doc_data["strategic_context"]),
                        },
                        "collaborations": {
                            "title": "Expected Collaborations",
                            "data": apply_styling(doc_data["collaborations"]),
                        },
                        "staff_time_allocation": {
                            "title": "Staff Time Allocation",
                            "data": generate_html_table_from_json_data(
                                apply_styling(doc_data["staff_time_allocation"])
                            ),
                        },
                        "indicative_operating_budget": {
                            "title": "Budget",
                            "data": generate_html_table_from_json_data(
                                apply_styling(doc_data["indicative_operating_budget"])
                            ),
                        },
                    },
                }
            )

        elif document_type == "projectplan":
            doc_data = get_project_plan_data()
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    "fonts_folder_path": fonts_folder_path,
                    "departmental_service_name": doc_data["departmental_service_name"],
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "methodology_image": doc_data["methodology_image"],
                    "html_data_items": {
                        "background": {
                            "title": "Background",
                            "data": apply_styling(doc_data["background"]),
                        },
                        "aims": {
                            "title": "Aims",
                            "data": apply_styling(doc_data["aims"]),
                        },
                        "outcomes": {
                            "title": "Expected Outcomes",
                            "data": apply_styling(doc_data["expected_outcomes"]),
                        },
                        "knowledge_transfer": {
                            "title": "Knowledge Transfer",
                            "data": apply_styling(doc_data["knowledge_transfer"]),
                        },
                        "project_tasks": {
                            "title": "Milestones",
                            "data": apply_styling(doc_data["project_tasks"]),
                        },
                        "listed_references": {
                            "title": "References",
                            "data": apply_styling(doc_data["listed_references"]),
                        },
                        "methodology": {
                            "title": "Methodology",
                            "data": apply_styling(doc_data["methodology"]),
                        },
                        "specimens": {
                            "title": "Number of Voucher Specimens",
                            "data": apply_styling(doc_data["specimens"]),
                        },
                        "data_management": {
                            "title": "Data Management",
                            "data": apply_styling(doc_data["data_management"]),
                        },
                        "related_projects": {
                            "title": "Related Science Projects",
                            "data": apply_styling(doc_data["related_projects"]),
                        },
                        "consolidated_funds": {
                            "title": "Consolidated Funds",
                            "data":
                            # generate_html_table_from_json_data(
                            apply_styling(doc_data["consolidated_funds"]),
                            # )
                        },
                        "external_funds": {
                            "title": "External Funds",
                            "data": generate_html_table_from_json_data(
                                # apply_styling(
                                doc_data["external_funds"]
                                # )
                            ),
                        },
                    },
                }
            )

        elif document_type == "progressreport":
            doc_data = get_progress_report_data()
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    "fonts_folder_path": fonts_folder_path,
                    "departmental_service_name": doc_data["departmental_service_name"],
                    "financial_year_string": doc_data["financial_year_string"],
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "context": {
                            "title": "Context",
                            "data": apply_styling(doc_data["context"]),
                        },
                        "aims": {
                            "title": "Aims",
                            "data": apply_styling(doc_data["aims"]),
                        },
                        "progress": {
                            "title": "Progress",
                            "data": apply_styling(doc_data["progress"]),
                        },
                        "implications": {
                            "title": "Management Implications",
                            "data": apply_styling(doc_data["implications"]),
                        },
                        "future": {
                            "title": "Future Directions",
                            "data": apply_styling(doc_data["future"]),
                        },
                    },
                }
            )
        elif document_type == "studentreport":
            doc_data = get_student_report_data()
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    "fonts_folder_path": fonts_folder_path,
                    "departmental_service_name": doc_data["departmental_service_name"],
                    "financial_year_string": doc_data["financial_year_string"],
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "progress_report": {
                            "title": "Progress Report",
                            "data": apply_styling(doc_data["progress_report"]),
                        },
                    },
                }
            )
        elif document_type == "projectclosure":
            doc_data = get_project_closure_data()
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    "fonts_folder_path": fonts_folder_path,
                    "departmental_service_name": doc_data["departmental_service_name"],
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "reason": {
                            "title": "Reason",
                            "data": apply_styling(doc_data["reason"]),
                        },
                        "knowledge_transfer": {
                            "title": "Knowledge Transfer",
                            "data": apply_styling(doc_data["knowledge_transfer"]),
                        },
                        "data_location": {
                            "title": "Data Location",
                            "data": apply_styling(doc_data["data_location"]),
                        },
                        "hardcopy_location": {
                            "title": "Hardcopy Location",
                            "data": apply_styling(doc_data["hardcopy_location"]),
                        },
                        "backup_location": {
                            "title": "Backup Location",
                            "data": apply_styling(doc_data["backup_location"]),
                        },
                        "scientific_outputs": {
                            "title": "Scientific Outputs",
                            "data": apply_styling(doc_data["scientific_outputs"]),
                        },
                        "intended_outcome": {
                            "title": "Intended Outcome",
                            "data": apply_styling(doc_data["intended_outcome"]),
                        },
                    },
                }
            )
        else:
            return Response(
                {"err": "Invalid project type"},
                HTTP_400_BAD_REQUEST,
            )

        # Combine all stylesheet paths into a single string separated by commas
        all_css_paths = ",".join([rte_css_path, prince_css_path])

        p = subprocess.Popen(
            ["prince", "-", f"--style={all_css_paths}", f"--javascript"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        outs, errs = p.communicate(f"{html_content}".encode("utf-8"))

        if p.returncode:
            # Handle `errs`.
            print(p.returncode)
            doc.pdf_generation_in_progress = True
            doc.save()

        else:
            pdf = outs
            print("PDF is " + str(len(pdf)) + " bytes in size")
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            if document_type == "progressreport" or document_type == "studentreport":
                pdf_filename = f'{doc_data["project_pk"]}_{document_kind_dict[document_type]} ({doc_data["financial_year_string"]}).pdf'
            else:
                pdf_filename = (
                    f'{doc_data["project_pk"]}_{document_kind_dict[document_type]}.pdf'
                )
            file_content = ContentFile(pdf, name=pdf_filename)

            doc.pdf_generation_in_progress = False
            doc.save()
            try:
                # Update item if it exists
                doc_pdf = ProjectDocumentPDF.objects.get(
                    document=doc, project=doc.project
                )

                ser = ProjectDocumentPDFSerializer(
                    doc_pdf,
                    data={
                        "file": file_content,
                    },
                    partial=True,
                )
                if ser.is_valid():
                    # Delete the previous file
                    pdfs_file_path = doc_pdf.file.path
                    default_storage.delete(pdfs_file_path)
                    doc_pdf = ser.save()
                    return Response(
                        ProjectDocumentPDFSerializer(doc_pdf).data,
                        status=HTTP_202_ACCEPTED,
                    )

                else:
                    print("Error saving PDF (try ser invalid)")
                    print(ser.errors)

            except ProjectDocumentPDF.DoesNotExist:
                # If the item doesn't exist, create a new one
                ser = ProjectDocumentPDFSerializer(
                    data={
                        "file": file_content,
                        "document": doc.pk,
                        "project": doc.project.pk,
                    }
                )
                if ser.is_valid():
                    doc_pdf = ser.save()
                    return Response(
                        ProjectDocumentPDFSerializer(doc_pdf).data,
                        status=HTTP_201_CREATED,
                    )
                else:
                    print("Error saving PDF (except ser invalid)")
                    print(ser.errors)

        return Response(
            {"error": True},
            status=HTTP_400_BAD_REQUEST,
        )


class CancelProjectDocGeneration(APIView):
    permission_classes = [IsAuthenticated]

    def get_main_doc(self, pk):
        # Gets the primary document that the concept plan belongs to
        try:
            doc = ProjectDocument.objects.filter(pk=pk).first()
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return doc

    def post(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is canceling PDF GEN for document {pk}")
        doc = self.get_main_doc(pk=pk)
        # doc.pdf_generation_in_progress = False
        # updated = doc.save()

        ser = ProjectDocumentSerializer(
            doc,
            data={"pdf_generation_in_progress": False},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            ser = ProjectDocumentSerializer(updated)
            settings.LOGGER.info(msg=f"Cancel Success")
            return Response(
                ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            print(ser.errors)
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


# endregion ==================================================


# region Publications ==================================================
class CustomPublications(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(f"{req.user} is getting CustomPublications")
        custom_publications = CustomPublication.objects.all()
        serializer = CustomPublicationSerializer(custom_publications, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, req):
        settings.LOGGER.info(f"{req.user} is creating a CustomPublication")

        serializer = CustomPublicationSerializer(data=req.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            settings.LOGGER.error(
                f"Error creating CustomPublication: {serializer.errors}"
            )
            print(req.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class CustomPublicationDetail(APIView):
    # permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = CustomPublication.objects.get(pk=pk)
        except CustomPublication.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        settings.LOGGER.info(f"{req.user} is getting CustomPublication {pk}")
        obj = self.go(req, pk)
        serializer = CustomPublicationSerializer(obj)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, req, pk):
        settings.LOGGER.info(f"{req.user} is updating CustomPublication {pk}")
        obj = self.go(pk)

        puplic_profile = obj.public_profile
        title = req.data.get("title")
        year = req.data.get("year")
        # print(req.data)

        serializer = CustomPublicationSerializer(
            obj,
            data={"title": title, "year": year, "public_profile": puplic_profile.pk},
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)

        settings.LOGGER.error(f"Error updating CustomPublication: {serializer.errors}")
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, req, pk):
        settings.LOGGER.info(f"{req.user} is deleting CustomPublication {pk}")
        obj = self.go(pk)
        obj.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class UserPublications(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def _error_response(self, message):
        return Response(
            {
                "staffProfilePk": 0,
                "libraryData": {
                    "numFound": 0,
                    "start": 0,
                    "numFoundExact": True,
                    "docs": [],
                    "isError": True,
                    "errorMessage": message,
                },
                "customPublications": [],
            },
            status=HTTP_200_OK,
        )

    def _get_library_publications(self, employee_id):
        api_url = f"{settings.LIBRARY_API_URL}{employee_id}&rows=1000"
        token = settings.LIBRARY_BEARER_TOKEN.replace("Bearer ", "")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            settings.LOGGER.error(
                f"Failed to retrieve data from API:\n{response.status_code}: {response.text}"
            )
            raise Exception(f"API request failed with status {response.status_code}")

        return response.json()

    def get(self, req, employee_id):
        settings.LOGGER.info(
            f"{req.user} is getting UserPublications for {employee_id}"
        )

        # Initial validation checks
        if not employee_id or employee_id == "null":
            return self._error_response("No employee ID provided")

        if not settings.LIBRARY_API_URL:
            return self._error_response("Library API configuration missing")

        if not settings.LIBRARY_BEARER_TOKEN:
            return self._error_response("Library Token configuration missing")

        # Check cache first
        cache_key = f"user_publications_{employee_id}"
        cached_data = cache.get(cache_key)

        # Get staff profile
        staff_profile = PublicStaffProfile.objects.filter(
            employee_id=employee_id
        ).first()

        # Get custom publications (needed for both cached and non-cached responses)
        custom_publications = CustomPublication.objects.filter(
            public_profile__employee_id=employee_id
        ).all()

        if cached_data:
            settings.LOGGER.info(f"Returning cached publications for {employee_id}")
            response_data = {
                "staffProfilePk": staff_profile.pk,
                "libraryData": cached_data,
                "customPublications": CustomPublicationSerializer(
                    custom_publications, many=True
                ).data,
            }
            return Response(response_data, status=HTTP_200_OK)

        try:
            # Get library publications
            library_data = self._get_library_publications(employee_id)

            # Get custom publications
            custom_publications = CustomPublication.objects.filter(
                public_profile__employee_id=employee_id
            ).all()

            # Process library data first
            library_response = {
                "numFound": library_data.get("response", {}).get("numFound", 0),
                "start": library_data.get("response", {}).get("start", 0),
                "numFoundExact": library_data.get("response", {}).get(
                    "numFoundExact", True
                ),
                "docs": library_data.get("response", {}).get("docs", []),
                "isError": False,
                "errorMessage": "",
            }

            # Serialize and cache library data
            library_serializer = LibraryPublicationResponseSerializer(
                data=library_response
            )
            if not library_serializer.is_valid():
                settings.LOGGER.error(
                    f"Library Serializer errors: {library_serializer.errors}"
                )
                return self._error_response("Invalid library data format")

            # Cache the library data
            cache.set(
                cache_key,
                library_serializer.data,
                timeout=timedelta(hours=24).total_seconds(),
            )

            # Combine everything for the final response
            response_data = {
                "staffProfilePk": staff_profile.pk,
                "libraryData": library_serializer.data,
                "customPublications": CustomPublicationSerializer(
                    custom_publications, many=True
                ).data,
            }

            # Final serialization for response format
            final_serializer = PublicationResponseSerializer(data=response_data)
            if not final_serializer.is_valid():
                settings.LOGGER.error(
                    f"Final Serializer errors: {final_serializer.errors}"
                )
                return self._error_response("Invalid response format")

            return Response(final_serializer.data, status=HTTP_200_OK)

        except Exception as e:
            settings.LOGGER.error(f"Error processing request: {str(e)}")
            return self._error_response("Failed to process request")


# endregion ==================================================

# region Document Approvals and Emails ==================================


class SendMentionNotification(APIView):
    """
    API endpoint for sending email notifications to mentioned users or default recipients.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Send email notifications to mentioned users or default recipients.

        Expected payload:
        {
            "documentId": 456,
            "projectId": 123,
            "commenter": {"id": 2, "name":"John Doe", "email":"john.doe@dbca.wa.gov.au"},
            "mentionedUsers": [{"id": 1, "name": "Test User","email": "user@dbca.wa.gov.au"}, ...],
            "documentKind": "concept",
            "commentContent": "<p>@Rory McAuley hi there</p>"
        }
        """
        try:
            # Extract data from request
            document_id = request.data.get("documentId")
            project_id = request.data.get("projectId")
            commenter = request.data.get("commenter")
            mentioned_users = request.data.get("mentionedUsers", [])
            comment_content = request.data.get("commentContent", "")

            # Fetch document and project information
            try:
                document = ProjectDocument.objects.get(pk=document_id)
                project = Project.objects.get(pk=project_id)
                project_tag = project.get_project_tag()
            except (ProjectDocument.DoesNotExist, Project.DoesNotExist) as e:
                settings.LOGGER.error(f"Document or Project not found: {e}")
                return Response(
                    {"error": "Document or Project not found"},
                    status=HTTP_404_NOT_FOUND,
                )

            # Generate the document URL
            url_safe_kind_dict = {
                "concept": "concept",
                "projectplan": "project",
                "progressreport": "progress",
                "studentreport": "student",
                "projectclosure": "closure",
            }

            document_url = f"{settings.SITE_URL}/projects/{project.pk}/{url_safe_kind_dict[document.kind]}"

            # Clean comment content for display (remove mention spans but keep text)
            def clean_comment_content(html_content):
                """Clean the comment content for email display"""
                from bs4 import BeautifulSoup

                if not html_content:
                    return ""

                try:
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Replace mention spans with just the text content
                    mention_spans = soup.find_all(
                        "span", {"data-lexical-mention": "true"}
                    )
                    for span in mention_spans:
                        span.replace_with(span.get_text())

                    # Get the cleaned text
                    cleaned_text = soup.get_text().strip()
                    return cleaned_text
                except Exception as e:
                    settings.LOGGER.error(f"Error cleaning comment content: {e}")
                    return html_content

            cleaned_comment = clean_comment_content(comment_content)

            # Only send emails if there are mentioned users
            if not mentioned_users:
                return Response(
                    {
                        "message": "No mentioned users found - no emails sent",
                        "recipients": 0,
                        "mentioned_users": 0,
                    },
                    status=HTTP_200_OK,
                )

            # Process mentioned users
            recipients_to_notify = []
            for user_data in mentioned_users:
                user_id = user_data.get("id")
                user_name = user_data.get("name")
                user_email = user_data.get("email")

                if user_email and user_email.endswith("@dbca.wa.gov.au"):
                    try:
                        # Validate user exists and is active
                        user = User.objects.get(pk=user_id)
                        if user.is_active and user.is_staff:
                            recipients_to_notify.append(
                                {"id": user_id, "name": user_name, "email": user_email}
                            )
                    except User.DoesNotExist:
                        settings.LOGGER.warning(f"Mentioned user {user_id} not found")
                        continue

            # Send emails
            processed_users = set()
            emails_sent = 0

            for recipient in recipients_to_notify:
                user_id = recipient.get("id")
                user_name = recipient.get("name")
                user_email = recipient.get("email")

                # Skip if already processed
                if user_id in processed_users:
                    continue

                processed_users.add(user_id)

                # Skip if not in production and not specific test user
                maintainer_pk = get_current_maintainer_pk()
                if (settings.ENVIRONMENT != "production") and user_id != maintainer_pk:
                    print(f"TEST: Skipping mention notification to {user_name}")
                    continue

                to_email = [user_email]
                document_kind_string_readable = ProjectDocument.CategoryKindChoices(
                    document.kind
                ).label

                # Email subject for mentions only
                email_subject = f"SPMS: You were mentioned in a comment on {document_kind_string_readable} ({project_tag})"

                template_props = {
                    "recipient_name": user_name,
                    "commenter_name": commenter.get("name"),
                    "document_type_title": document_kind_string_readable,
                    "project_tag": project_tag,
                    "project_name": project.title,
                    "document_url": document_url,
                    "comment_content": cleaned_comment,
                    "is_mention": True,  # Always true now since we only send for mentions
                    "site_url": settings.SITE_URL,
                    # "dbca_image_path": get_encoded_image(),
                }

                try:
                    template_content = render_to_string(
                        "./email_templates/document_comment_mention.html",
                        template_props,
                    )
                    send_email_with_embedded_image(
                        recipient_email=to_email,
                        subject=email_subject,
                        html_content=template_content,
                    )
                    emails_sent += 1
                    print(
                        f"{'PRODUCTION' if settings.ENVIRONMENT == 'production' else 'TEST'}: Sent comment notification to {user_name}"
                    )
                except Exception as e:
                    error_msg = f"Comment Notification Email Error: {e}"
                    settings.LOGGER.error(error_msg)

            return Response(
                {
                    "message": f"Mention notifications sent to {emails_sent} users",
                    "recipients": len(recipients_to_notify),
                    "mentioned_users": len(mentioned_users),
                },
                status=HTTP_200_OK,
            )

        except Exception as e:
            settings.LOGGER.error(f"Error sending comment notifications: {str(e)}")
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)


class BaseDocumentAction(APIView):
    permission_classes = [IsAuthenticated]

    # Validation
    def get_document(self, pk):
        settings.LOGGER.info("DOC ACTION: Getting document")
        try:
            return ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound

    def validate_request_data(self, req):
        """Validate basic params in req data"""
        settings.LOGGER.info("DOC ACTION: Validating req data")

        stage = req.data.get("stage")
        document_pk = req.data.get("documentPk")
        if not stage or not document_pk:
            settings.LOGGER.info(
                f"{req.user} failed in doc action: no stage/document pk"
            )
            return None, None

        stage = int(stage) if stage else None
        return stage, document_pk

    # Document and Project Update Methods
    def update_document(self, document, data, user):
        """Update document with provided data"""
        settings.LOGGER.info("DOC ACTION: Updating doc data")

        ser = ProjectDocumentSerializer(
            document,
            data=data,
            partial=True,
        )

        if not ser.is_valid():
            settings.LOGGER.error(f"Validation error: {ser.errors}")
            return None, ser.errors

        return ser.save(), None

    def handle_project_status_update(self, document, stage):
        """Update project status based on document kind and stage"""
        settings.LOGGER.info("DOC ACTION: Updating Project Status")

        if stage != 3:
            return

        kind = document.kind
        project = document.project

        status_mapping = {
            "projectplan": Project.StatusChoices.UPDATING,
            "progressreport": Project.StatusChoices.ACTIVE,
            "studentreport": Project.StatusChoices.ACTIVE,
        }

        if kind in status_mapping:
            project.status = status_mapping[kind]
            project.save()
        elif kind == "projectclosure":
            settings.LOGGER.info(f"Closing Project via {kind} document")
            closure_doc = ProjectClosure.objects.get(document=document)
            project.status = closure_doc.intended_outcome
            project.save()

    # Template Population
    def get_default_budget_template(self):
        """Return the default budget template HTML"""
        settings.LOGGER.info("DOC ACTION: Getting default budget template")

        return """
        <table class="table-light">
            <colgroup>
                <col>
                <col>
                <col>
                <col>
            </colgroup>
            <tbody>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Source</span>
                        </p>
                    </th>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Year 1</span>
                        </p>
                    </th>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Year 2</span>
                        </p>
                    </th>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Year 3</span>
                        </p>
                    </th>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">FTE Scientist</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">FTE Technical</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Equipment</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Vehicle</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Travel</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Other</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Total</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
            </tbody>
        </table>
        """

    def get_default_external_budget_template(self):
        """Return the default external budget template HTML"""
        settings.LOGGER.info("DOC ACTION: Getting default external budget template")
        return """
        <table class="table-light">
            <colgroup>
                <col>
                <col>
                <col>
                <col>
            </colgroup>
            <tbody>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Source</span>
                        </p>
                    </th>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Year 1</span>
                        </p>
                    </th>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Year 2</span>
                        </p>
                    </th>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Year 3</span>
                        </p>
                    </th>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Salaries, Wages, Overtime</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Overheads</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Equipment</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Vehicle</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Travel</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Other</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
                <tr>
                    <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">
                        <p class="editor-p-light" dir="ltr">
                            <span style="white-space: pre-wrap;">Total</span>
                        </p>
                    </th>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                    <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>
                </tr>
            </tbody>
        </table>
        """

    def get_default_project_plan_data(self, project_pk, document_pk):
        """Return default data for a new project plan"""
        settings.LOGGER.info("DOC ACTION: Getting default project plan data")
        return {
            "document": document_pk,
            "project": project_pk,
            "background": "<p></p>",
            "methodology": "<p></p>",
            "aims": "<p></p>",
            "outcome": "<p></p>",
            "knowledge_transfer": "<p></p>",
            "listed_references": "<p></p>",
            "operating_budget": self.get_default_budget_template(),
            "operating_budget_external": self.get_default_external_budget_template(),
            "related_projects": "<p></p>",
        }

    # Email methods
    def should_send_emails(self, document, req):
        """Determine if emails should be sent (based on req and conditions)"""
        settings.LOGGER.info("DOC ACTION: Determining if should send email")

        # First check if the request explicitly says not to send emails
        should_send = req.data.get("shouldSendEmail")
        if not should_send or should_send == "false":
            settings.LOGGER.info(
                "DETERMINATION: Request explicitly says not to send email, so no emails"
            )
            return False

        # Check if the project has required participants
        project = document.project

        # Check if business area leader exists
        try:
            if not project.business_area or not project.business_area.leader:
                settings.LOGGER.info(
                    "DETERMINATION: No business area leader found, so no emails"
                )
                return False
        except Exception as e:
            settings.LOGGER.error(f"Error checking business area leader: {e}")
            return False

        # Check if project leader exists (for applicable actions)
        try:
            project_leader_exists = ProjectMember.objects.filter(
                project=project, is_leader=True
            ).exists()

            if not project_leader_exists:
                settings.LOGGER.info(
                    "DETERMINATION: No project leader found, so no emails"
                )
                return False
        except Exception as e:
            settings.LOGGER.error(f"Error checking project leader: {e}")
            return False

        # Check if directorate list exists (for stage 2 approvals)
        try:
            division = project.business_area.division
            if not division or not division.directorate_email_list.exists():
                settings.LOGGER.info(
                    "DETERMINATION: No directorate list for division, so no emails"
                )
                return False
        except Exception as e:
            settings.LOGGER.error(f"Error checking directorate list: {e}")
            return False

        # All checks passed, should send email
        settings.LOGGER.info("DETERMINATION: All checks passed, should send emails")
        return True

    def get_email_recipients(self, document, stage, action_type):
        """Get list of email recipients based on document, stage and action type"""
        settings.LOGGER.info("DOC ACTION: Getting email recipients")

        project = document.project
        recipients_list = []

        if stage == 1:  # Project Lead Action: stage one always sends emails to ba lead
            # BA Lead
            ba_lead = User.objects.get(pk=project.business_area.leader.pk)
            recipients_list.append(
                {
                    "pk": ba_lead.pk,
                    "name": f"{ba_lead.display_first_name} {ba_lead.display_last_name}",
                    "email": ba_lead.email,
                }
            )

        elif stage == 2:  # BA Lead Action
            if (
                action_type == "approve"
            ):  # if approving on stage 2, sends to divisional directorate
                # Directorate email list
                division = project.business_area.division
                for member in division.directorate_email_list.all():
                    if member.is_active and member.is_staff:
                        recipients_list.append(
                            {
                                "pk": member.pk,
                                "name": f"{member.display_first_name} {member.display_last_name}",
                                "email": member.email,
                            }
                        )
            elif action_type in [
                "recall",
                "send_back",
            ]:  # if recalling or sending back, sends to project lead
                # Project Leader
                p_leader = ProjectMember.objects.get(project=project, is_leader=True)
                recipients_list.append(
                    {
                        "pk": p_leader.user.pk,
                        "name": f"{p_leader.user.display_first_name} {p_leader.user.display_last_name}",
                        "email": p_leader.user.email,
                    }
                )

        elif stage == 3:  # Divisional Directorate Action
            if action_type == "approve":  # Alert project lead and ba lead
                # Project Leader and BA Lead
                p_leader = ProjectMember.objects.get(project=project, is_leader=True)
                recipients_list.append(
                    {
                        "pk": p_leader.user.pk,
                        "name": f"{p_leader.user.display_first_name} {p_leader.user.display_last_name}",
                        "email": p_leader.user.email,
                    }
                )

                ba_lead = User.objects.get(pk=project.business_area.leader.pk)
                recipients_list.append(
                    {
                        "pk": ba_lead.pk,
                        "name": f"{ba_lead.display_first_name} {ba_lead.display_last_name}",
                        "email": ba_lead.email,
                    }
                )
            elif action_type in ["recall", "send_back"]:  # alert ba lead
                # BA Lead
                ba_lead = User.objects.get(pk=project.business_area.leader.pk)
                recipients_list.append(
                    {
                        "pk": ba_lead.pk,
                        "name": f"{ba_lead.display_first_name} {ba_lead.display_last_name}",
                        "email": ba_lead.email,
                    }
                )

        # Deduplication step
        seen_pks = set()
        deduplicated_list = []

        for recipient in recipients_list:
            if recipient["pk"] not in seen_pks:
                seen_pks.add(recipient["pk"])
                deduplicated_list.append(recipient)

        # Return deduplicated list
        return deduplicated_list

    def get_email_template_and_subject(self, document, stage, action_type):
        """Get email template path and subject based on document, stage and action type"""
        settings.LOGGER.info("DOC ACTION: Getting email template and subject")
        kind = document.kind
        project = document.project
        project_tag = project.get_project_tag()

        document_kind_dict = {
            "concept": "Science Concept Plan",
            "projectplan": "Science Project Plan",
            "progressreport": "Progress Report",
            "studentreport": "Student Report",
            "projectclosure": "Project Closure",
        }
        document_kind_as_title = document_kind_dict.get(kind, "Document")

        template_path = None
        subject = None

        if action_type == "approve":
            if stage == 3 and kind == "projectclosure":
                template_path = "./email_templates/project_closed_email.html"
            elif stage == 3:
                template_path = (
                    "./email_templates/document_approved_directorate_email.html"
                )
            else:
                template_path = "./email_templates/document_approved_email.html"

            subject = f"SPMS: {document_kind_as_title} Approved ({project_tag})"

        elif action_type == "recall":
            if stage == 3 and kind == "projectclosure":
                template_path = "./email_templates/project_reopened_email.html"
                subject = f"SPMS: {project_tag} Re-Opened"
            else:
                template_path = "./email_templates/document_recalled_email.html"
                subject = f"SPMS: {document_kind_as_title} Recalled ({project_tag})"

        elif action_type == "send_back":
            template_path = "./email_templates/document_sent_back_email.html"
            subject = f"SPMS: {document_kind_as_title} Sent Back ({project_tag})"

        elif action_type == "reopen":
            template_path = "./email_templates/project_reopened_email.html"
            subject = f"SPMS: {project_tag} Re-Opened"

        return template_path, subject

    def send_emails(
        self, document, stage, user, recipients_list, action_type, feedback_html=None
    ):
        """Send emails to recipients"""
        settings.LOGGER.info("DOC ACTION: Sending email to recipients")
        if not recipients_list:
            return "No recipients found", HTTP_202_ACCEPTED

        maintainer_pk = get_current_maintainer_pk()

        project = document.project
        template_path, email_subject = self.get_email_template_and_subject(
            document, stage, action_type
        )

        if not template_path or not email_subject:
            return "Email template not found", HTTP_400_BAD_REQUEST

        # User info
        actioning_user_name = f"{user.display_first_name} {user.display_last_name}"
        actioning_user_email = user.email

        document_kind_dict = {
            "concept": "Science Concept Plan",
            "projectplan": "Science Project Plan",
            "progressreport": "Progress Report",
            "studentreport": "Student Report",
            "projectclosure": "Project Closure",
        }
        document_kind_as_title = document_kind_dict.get(document.kind, "Document")

        processed = []
        for recipient in recipients_list:
            if recipient["pk"] in processed:
                continue

            processed.append(recipient["pk"])

            # Skip if not in production and not specific test user (maintainer - adjust)
            # TODO: Adjust to user set as maintainer isntead of hardcode
            if (
                settings.ENVIRONMENT == "staging"
                or settings.ENVIRONMENT == "development"
            ) and recipient["pk"] != maintainer_pk:
                print(f"TEST: Skipping email to {recipient['name']}")
                continue

            to_email = [recipient["email"]]

            template_props = {
                "stage": stage,
                "actioning_user_email": actioning_user_email,
                "actioning_user_name": actioning_user_name,
                "email_subject": email_subject,
                "recipient_name": recipient["name"],
                "project_id": project.pk,
                "plain_project_name": project.title,
                "document_type": determine_doc_kind_url_string(document.kind),
                "document_type_title": document_kind_as_title,
                "site_url": settings.SITE_URL,
                "dbca_image_path": get_encoded_image(),
            }

            # Add feedback HTML if provided
            if feedback_html:
                template_props["feedback_html"] = feedback_html

            # Add action-specific template variables
            if action_type in ["recall", "send_back"]:
                template_props["user_kind"] = (
                    "Project Lead" if stage == 2 else "Business Area Lead"
                )

            try:
                template_content = render_to_string(template_path, template_props)
                send_email_with_embedded_image(
                    recipient_email=to_email,
                    subject=email_subject,
                    html_content=template_content,
                )
                print(
                    f"{'PRODUCTION' if not settings.DEBUG else 'TEST'}: Sent email to {recipient['name']}"
                )
            except Exception as e:
                error_msg = f"Email Error: {e}"
                if "getaddrinfo" in str(e):
                    error_msg += "\nIf this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters."
                settings.LOGGER.error(error_msg)
                return str(e), HTTP_400_BAD_REQUEST

        return "Emails Sent!", HTTP_202_ACCEPTED


class DocApproval(BaseDocumentAction):
    def get_approval_data(self, stage, user_pk):
        """Return appropriate data dict based on approval stage"""
        settings.LOGGER.info("DOC ACTION: Getting approval data")
        stage = int(stage)

        if stage == 1:
            return {
                "project_lead_approval_granted": True,
                "modifier": user_pk,
                "status": "inapproval",
            }
        elif stage == 2:
            return {
                "business_area_lead_approval_granted": True,
                "modifier": user_pk,
                "status": "inapproval",
            }
        elif stage == 3:
            return {
                "directorate_approval_granted": True,
                "modifier": user_pk,
                "status": "approved",
            }
        else:
            settings.LOGGER.error(f"Invalid approval stage: {stage}")
            raise ValidationError(f"Invalid approval stage: {stage}")

    def create_project_plan_if_needed(self, concept_document, user):
        """Create a project plan if one doesn't already exist"""
        project_pk = concept_document.project.pk

        # Check if project plan already exists
        if ProjectPlan.objects.filter(project=project_pk).exists():
            return True

        # Create new project plan document
        with transaction.atomic():
            try:
                document_data = {
                    "old_id": 1,
                    "kind": "projectplan",
                    "status": "new",
                    "project": project_pk,
                    "creator": user.pk,
                    "modifier": user.pk,
                }

                document_serializer = ProjectDocumentCreateSerializer(
                    data=document_data
                )
                if not document_serializer.is_valid():
                    settings.LOGGER.error(
                        f"Project plan document creation error: {document_serializer.errors}"
                    )
                    return False

                projplanmaindoc = document_serializer.save()

                # Create project plan with default content
                plan_data = self.get_default_project_plan_data(
                    project_pk, projplanmaindoc.pk
                )
                project_plan_serializer = ProjectPlanCreateSerializer(data=plan_data)

                if not project_plan_serializer.is_valid():
                    settings.LOGGER.error(
                        f"Project plan creation error: {project_plan_serializer.errors}"
                    )
                    return False

                projplan = project_plan_serializer.save()

                # Create endorsements
                endorsement_data = {
                    "project_plan": projplan.pk,
                    "ae_endorsement_required": False,
                    "ae_endorsement_provided": False,
                    "data_management": "<p></p>",
                    "no_specimens": "<p></p>",
                }

                endorsements = EndorsementCreationSerializer(data=endorsement_data)
                if not endorsements.is_valid():
                    settings.LOGGER.error(
                        f"Endorsement creation error: {endorsements.errors}"
                    )
                    return False

                endorsements.save()

                # Update project status
                concept_document.project.status = Project.StatusChoices.PENDING
                concept_document.project.save()

                return True

            except Exception as e:
                settings.LOGGER.error(f"Error creating project plan: {e}")
                return False

    def post(self, req):
        """Handle document approval"""
        try:
            # Validate basic parameters
            stage, document_pk = self.validate_request_data(req)
            if not stage or not document_pk:
                return Response(status=HTTP_400_BAD_REQUEST)

            document = self.get_document(pk=document_pk)
            settings.LOGGER.info(f"{req.user} is approving {document}")

            # Get approval data based on stage
            approval_data = self.get_approval_data(stage, req.user.pk)

            # Update document with approval data
            updated_document, errors = self.update_document(
                document, approval_data, req.user
            )
            if errors:
                return Response(errors, status=HTTP_400_BAD_REQUEST)

            # Special handling for stage 3 concept documents - create project plan
            if updated_document.kind == "concept" and stage == 3:
                if not self.create_project_plan_if_needed(updated_document, req.user):
                    return Response(
                        "Failed to create project plan", status=HTTP_400_BAD_REQUEST
                    )

            # Handle project status updates
            self.handle_project_status_update(updated_document, stage)

            # Check if emails should be sent
            if self.should_send_emails(updated_document, req):
                # Get feedback HTML if provided
                feedback_html = req.data.get("feedbackHTML")

                recipients = self.get_email_recipients(
                    updated_document, stage, "approve"
                )
                message, status = self.send_emails(
                    updated_document,
                    stage,
                    req.user,
                    recipients,
                    "approve",
                    feedback_html,
                )

                if status != HTTP_202_ACCEPTED:
                    return Response({"error": message}, status=status)

                return Response(message, status=status)

            # Return updated document
            return Response(
                TinyProjectDocumentSerializer(updated_document).data,
                status=HTTP_202_ACCEPTED,
            )

        except ValidationError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            settings.LOGGER.error(f"Unexpected error in DocApproval: {e}")
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)


class DocRecall(BaseDocumentAction):
    def get_recall_data(self, stage, user_pk, document):
        """Return appropriate data dict based on recall stage"""
        settings.LOGGER.info("DOC ACTION: Getting recall data")
        stage = int(stage)

        if stage == 1:
            if document.business_area_lead_approval_granted == False:
                return {
                    "project_lead_approval_granted": False,
                    "modifier": user_pk,
                    "status": "revising",
                }
        elif stage == 2:
            if document.directorate_approval_granted == False:
                return {
                    "business_area_lead_approval_granted": False,
                    "modifier": user_pk,
                    "status": "inapproval",
                }
        elif stage == 3:
            return {
                "directorate_approval_granted": False,
                "modifier": user_pk,
                "status": "inapproval",
            }

        return None

    def post(self, req):
        """Handle document recall"""
        try:
            # Validate basic parameters
            stage, document_pk = self.validate_request_data(req)
            if not stage or not document_pk:
                return Response(status=HTTP_400_BAD_REQUEST)

            document = self.get_document(pk=document_pk)
            settings.LOGGER.info(f"{req.user} is recalling {document}")

            # Get recall data based on stage
            recall_data = self.get_recall_data(stage, req.user.pk, document)
            if not recall_data:
                return Response(
                    "Invalid recall stage or document state",
                    status=HTTP_400_BAD_REQUEST,
                )

            # Update document with recall data
            updated_document, errors = self.update_document(
                document, recall_data, req.user
            )
            if errors:
                return Response(errors, status=HTTP_400_BAD_REQUEST)

            # Handle project status updates based on document kind
            if updated_document.kind == "projectplan" and stage == 3:
                updated_document.project.status = Project.StatusChoices.PENDING
                updated_document.project.save()
            elif updated_document.kind == "projectclosure" and stage == 3:
                updated_document.project.status = Project.StatusChoices.CLOSUREREQ
                updated_document.project.save()
            elif (
                updated_document.kind in ["progressreport", "studentreport"]
                and stage == 3
            ):
                updated_document.project.status = Project.StatusChoices.UPDATING
                updated_document.project.save()

            # Check if emails should be sent
            if self.should_send_emails(updated_document, req):
                # Get feedback HTML if provided
                feedback_html = req.data.get("feedbackHTML")

                recipients = self.get_email_recipients(
                    updated_document, stage, "recall"
                )
                message, status = self.send_emails(
                    updated_document,
                    stage,
                    req.user,
                    recipients,
                    "recall",
                    feedback_html,
                )

                if status != HTTP_202_ACCEPTED:
                    return Response({"error": message}, status=status)

                return Response(message, status=status)

            # Return updated document
            return Response(
                TinyProjectDocumentSerializer(updated_document).data,
                status=HTTP_202_ACCEPTED,
            )

        except Exception as e:
            settings.LOGGER.error(f"Unexpected error in DocRecall: {e}")
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)


class DocSendBack(BaseDocumentAction):
    def get_send_back_data(self, stage, user_pk):
        """Return appropriate data dict based on send back stage"""
        settings.LOGGER.info("DOC ACTION: Getting send back data")
        stage = int(stage)

        if stage == 2:
            return {
                "business_area_lead_approval_granted": False,
                "project_lead_approval_granted": False,
                "modifier": user_pk,
                "status": "revising",
            }
        elif stage == 3:
            return {
                "business_area_lead_approval_granted": False,
                "directorate_approval_granted": False,
                "modifier": user_pk,
                "status": "revising",
            }

        return None

    def post(self, req):
        """Handle document send back"""
        try:
            # Validate basic parameters
            stage, document_pk = self.validate_request_data(req)
            if not stage or not document_pk:
                return Response(status=HTTP_400_BAD_REQUEST)

            document = self.get_document(pk=document_pk)
            settings.LOGGER.info(f"{req.user} is sending back {document}")

            # Get send back data based on stage
            send_back_data = self.get_send_back_data(stage, req.user.pk)
            if not send_back_data:
                return Response("Invalid send back stage", status=HTTP_400_BAD_REQUEST)

            # Update document with send back data
            updated_document, errors = self.update_document(
                document, send_back_data, req.user
            )
            if errors:
                return Response(errors, status=HTTP_400_BAD_REQUEST)

            # Check if emails should be sent
            if self.should_send_emails(updated_document, req):
                # Get feedback HTML if provided
                feedback_html = req.data.get("feedbackHTML")

                recipients = self.get_email_recipients(
                    updated_document, stage, "send_back"
                )
                message, status = self.send_emails(
                    updated_document,
                    stage,
                    req.user,
                    recipients,
                    "send_back",
                    feedback_html,
                )

                if status != HTTP_202_ACCEPTED:
                    return Response({"error": message}, status=status)

                return Response(message, status=status)

            # Return updated document
            return Response(
                TinyProjectDocumentSerializer(updated_document).data,
                status=HTTP_202_ACCEPTED,
            )

        except Exception as e:
            settings.LOGGER.error(f"Unexpected error in DocSendBack: {e}")
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)


class DocReopenProject(BaseDocumentAction):
    def post(self, req):
        """Handle project reopening by deleting closure document"""
        try:
            # Validate basic parameters
            stage, document_pk = self.validate_request_data(req)
            if not stage or not document_pk:
                settings.LOGGER.error("Error reopening - no stage/doc pk")
                return Response(status=HTTP_400_BAD_REQUEST)

            document = self.get_document(pk=document_pk)
            settings.LOGGER.info(
                f"{req.user} is reopening project by deleting closure for {document.project}"
            )

            # Update project status
            project = document.project
            project.status = "updating"
            project.save()

            # Delete the closure document
            closure = ProjectClosure.objects.get(document=document)
            closure.delete()
            document.delete()

            # Check if emails should be sent
            if self.should_send_emails(document, req):
                # Get feedback HTML if provided
                feedback_html = req.data.get("feedbackHTML")

                # For reopen, recipients are different - just the project leader
                p_leader = ProjectMember.objects.get(project=project, is_leader=True)
                recipients = [
                    {
                        "pk": p_leader.user.pk,
                        "name": f"{p_leader.user.display_first_name} {p_leader.user.display_last_name}",
                        "email": p_leader.user.email,
                    }
                ]

                message, status = self.send_emails(
                    document,
                    stage,
                    req.user,
                    recipients,
                    "reopen",
                    feedback_html,
                )

                if status != HTTP_202_ACCEPTED:
                    return Response({"error": message}, status=status)

                return Response(message, status=status)

            return Response(status=HTTP_204_NO_CONTENT)

        except Exception as e:
            settings.LOGGER.error(f"Unexpected error in DocReopenProject: {e}")
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)


# endregion =============================================================


# region Emails (NOTE: Separate email logic in Document Approvals and email region )==========================================================


class GetProjectLeadEmail(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is requesting active project lead emails to send a message to"
        )
        states = [
            Project.StatusChoices.ACTIVE,
            Project.StatusChoices.UPDATING,
            Project.StatusChoices.SUSPENDED,
        ]
        activeproj_leaders = ProjectMember.objects.filter(
            is_leader=True, project__status__in=states
        ).all()
        unique_active_project_leads = list(
            set(
                lead_member_object.user
                for lead_member_object in activeproj_leaders
                if lead_member_object.user.is_active
                and lead_member_object.user.is_staff
            )
        )
        unique_inactive_leads = list(
            set(
                lead_member_object.user
                for lead_member_object in activeproj_leaders
                if not lead_member_object.user.is_active
                or not lead_member_object.user.is_staff
            )
        )

        file_content = []

        dbca_users = []
        dbca_emails = []
        other_users = []
        other_emails = []

        inactive_leaders = []

        file_content.append(
            "-------------------------------------------------------------------------------------\nUnique Project Leads marked as staff and active (For Active, Suspended, Update Requested Projects)\n-------------------------------------------------------------------------------------\n"
        )

        for leader in unique_active_project_leads:
            if leader.email.endswith("dbca.wa.gov.au"):
                dbca_users.append(leader)

            else:
                other_users.append(leader)

        file_content.append(
            "------\nWith DBCA EMAIL (For Active, Suspended, Update Requested Projects)\n------\n"
        )

        for user in dbca_users:
            file_content.append(f"{user.email}\n")
            image = user.get_image()
            dbca_emails.append(
                {
                    "pk": user.pk,
                    "name": f"{user.display_first_name} {user.display_last_name}",
                    "email": f"{user.email}",
                    "is_staff": user.is_staff,
                    "is_active": user.is_active,
                    "image": image["file"] if image is not None else None,
                }
            )

        file_content.append(
            "\n------\nWith NON-DBCA EMAIL (For Active, Suspended, Update Requested Projects)\n------\n"
        )

        for user in other_users:
            file_content.append(f"{user.email}\n")
            other_emails.append({user.email})

        file_content.append(
            "\n\n-------------------------------------------------------------------------------------\nUnique Project Leads marked as NOT staff or INACTIVE (For Active, Suspended, Update Requested Projects)\n-------------------------------------------------------------------------------------\n"
        )
        for leader in unique_inactive_leads:
            inactive_leaders.append(leader)

        inactive_email_list = []
        for leader in inactive_leaders:
            image = leader.get_image()
            inactive_email_list.append(
                {
                    "pk": leader.pk,
                    "name": f"{leader.display_first_name} {leader.display_last_name}",
                    "email": f"{leader.email}",
                    "is_staff": leader.is_staff,
                    "is_active": leader.is_active,
                    "image": image["file"] if image is not None else None,
                }
            )
            projects_belonging_to = activeproj_leaders.filter(user=leader).all()
            file_content.append(
                f"\nUser: {leader.email} | {leader.display_first_name} {leader.display_last_name}\nProjects Led:\n"
            )
            for p in projects_belonging_to:
                file_content.append(
                    f"\t-Link: {settings.SITE_URL}/projects/{p.project.pk}\n"
                )
                file_content.append(f"\t-Project: {p.project.title}\n\n")

            file_content.append("\n")

        return_data = {
            "file_content": file_content,
            "unique_dbca_emails_list": dbca_emails,
            "unique_non_dbca_emails_list": inactive_email_list,
        }
        settings.LOGGER.warning(msg=f"{req.user} has been sent the email list")
        return Response(
            data=return_data,
            status=HTTP_200_OK,
        )


class SPMSInviteEmail(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (SPMS Invite Link) for users {req.data['invitee']}"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        inviting_email = req.data["invitor"]
        templ = "./email_templates/spms_link_email.html"
        invitee = req.data["invitee"]

        recipients_list = []
        # Validate
        if invitee.endswith("@dbca.wa.gov.au"):
            recipients_list.append(invitee)

        processed = []
        for recipient in recipients_list:
            if recipient not in processed:
                if settings.ENVIRONMENT == "production":
                    print(f"PRODUCTION: Sending email to {recipient}")
                    email_subject = f"SPMS Invite"
                    to_email = [recipient]

                    template_props = {
                        "inviting_email": inviting_email,
                        "email_subject": email_subject,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    template_content = render_to_string(templ, template_props)

                    try:
                        send_email_with_embedded_image(
                            recipient_email=to_email,
                            subject=email_subject,
                            html_content=template_content,
                        )
                        # send_mail(
                        #     email_subject,
                        #     template_content,
                        #     from_email,
                        #     to_email,
                        #     fail_silently=False,
                        #     html_message=template_content,
                        # )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
                else:
                    # test
                    print(f"TEST: Sending email to {recipient}")
                    if recipient == settings.SPMS_MAINTAINER_EMAIL:
                        email_subject = f"SPMS Invite"
                        to_email = [recipient]

                        template_props = {
                            "inviting_email": inviting_email,
                            "email_subject": email_subject,
                            "site_url": settings.SITE_URL,
                            "dbca_image_path": get_encoded_image(),
                        }

                        template_content = render_to_string(templ, template_props)

                        try:
                            send_email_with_embedded_image(
                                recipient_email=to_email,
                                subject=email_subject,
                                html_content=template_content,
                            )
                            # send_mail(
                            #     email_subject,
                            #     template_content,
                            #     from_email,
                            #     to_email,
                            #     fail_silently=False,
                            #     html_message=template_content,
                            # )
                        except Exception as e:
                            settings.LOGGER.error(
                                msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                            )
                            return Response(
                                {"error": str(e)},
                                status=HTTP_400_BAD_REQUEST,
                            )
                processed.append(recipient)
                print(f"Sent invite to {recipient}")

        return Response(
            "Email Sent!",
            status=HTTP_202_ACCEPTED,
        )


# Emails admin part
class NewCycleOpenEmail(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (New Cycle Open) to Project Leads for active projects and all Business Area Leaders"
        )

        maintainer_pk = get_current_maintainer_pk()

        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/new_cycle_open_email.html"

        # Get recipient list (ba leads)
        ba_leads = {ba.leader.pk for ba in BusinessArea.objects.all() if ba.leader}
        # Get recipient list (active project leads)
        also_updating = req.data["include_projects_with_status_updating"]
        if also_updating == True or also_updating == "True":
            active_project_leads = (
                ProjectMember.objects.filter(
                    project__status__in=[
                        Project.StatusChoices.ACTIVE,
                        Project.StatusChoices.UPDATING,
                    ],
                    is_leader=True,
                )
                .values_list("user__pk", flat=True)
                .distinct()
            )
        else:
            active_project_leads = (
                ProjectMember.objects.filter(
                    project__status__in=[Project.StatusChoices.ACTIVE], is_leader=True
                )
                .values_list("user__pk", flat=True)
                .distinct()
            )

        # Get combined recipient list, without duplicates
        recipients_list_data = list(ba_leads.union(active_project_leads))

        print(recipients_list_data)

        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.display_first_name} {user.display_last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get FY information
        financial_year = req.data["financial_year"]
        financial_year_string = f"{int(financial_year-1)}-{int(financial_year)}"

        processed = []
        for recipient in recipients_list:
            if recipient["pk"] not in processed:
                if settings.ENVIRONMENT == "production":
                    print(f"PRODUCTION: Sending email to {recipient["name"]}")

                    email_subject = (
                        f"SPMS: {financial_year_string} Reporting Cycle Open"
                    )
                    to_email = [recipient["email"]]

                    template_props = {
                        "email_subject": email_subject,
                        "recipient_name": recipient["name"],
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                        "financial_year_string": financial_year_string,
                    }

                    template_content = render_to_string(templ, template_props)

                    try:
                        send_email_with_embedded_image(
                            recipient_email=to_email,
                            subject=email_subject,
                            html_content=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
                else:
                    # test
                    print(f"TEST: Sending email to {recipient["name"]}")
                    if recipient["pk"] == maintainer_pk:
                        email_subject = (
                            f"SPMS: {financial_year_string} Reporting Cycle Open"
                        )
                        to_email = [recipient["email"]]

                        template_props = {
                            "email_subject": email_subject,
                            "recipient_name": recipient["name"],
                            "site_url": settings.SITE_URL,
                            "dbca_image_path": get_encoded_image(),
                            "financial_year_string": financial_year_string,
                        }

                        template_content = render_to_string(templ, template_props)

                        try:
                            send_email_with_embedded_image(
                                recipient_email=to_email,
                                subject=email_subject,
                                html_content=template_content,
                            )
                        except Exception as e:
                            settings.LOGGER.error(
                                msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                            )
                            return Response(
                                {"error": str(e)},
                                status=HTTP_400_BAD_REQUEST,
                            )
                processed.append(recipient["pk"])

        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


# endregion EMAILS ==========================================================
