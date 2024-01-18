import datetime
import logging
import os
import time
from django.shortcuts import render
from communications.models import Comment
from communications.serializers import (
    TinyCommentCreateSerializer,
    TinyCommentSerializer,
)

# from config.tasks import generate_pdf
from projects.models import Project, ProjectMember

from medias.models import AECEndorsementPDF, AnnualReportPDF, ProjectDocumentPDF
from medias.serializers import (
    AECPDFCreateSerializer,
    ProjectDocumentPDFSerializer,
    TinyAnnualReportPDFSerializer,
)
from users.models import User, UserWork
from .models import (
    ConceptPlan,
    ProgressReport,
    ProjectClosure,
    ProjectPlan,
    StudentReport,
    ProjectDocument,
    AnnualReport,
    Endorsement,
    Publication,
)
from django.db.models import Q, F

from .serializers import (
    AnnualReportSerializer,
    ConceptPlanCreateSerializer,
    ConceptPlanSerializer,
    EndorsementCreationSerializer,
    EndorsementSerializer,
    MiniAnnualReportSerializer,
    ProgressReportCreateSerializer,
    ProgressReportSerializer,
    ProjectClosureCreationSerializer,
    ProjectClosureSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
    ProjectPlanCreateSerializer,
    ProjectPlanSerializer,
    PublicationSerializer,
    StudentReportCreateSerializer,
    StudentReportSerializer,
    TinyAnnualReportSerializer,
    TinyConceptPlanSerializer,
    TinyEndorsementSerializer,
    TinyProgressReportSerializer,
    TinyProjectClosureSerializer,
    TinyProjectDocumentSerializer,
    TinyProjectPlanSerializer,
    TinyPublicationSerializer,
    TinyStudentReportSerializer,
)


# Create your views here.
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
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from django.db.models import Max

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django.db import transaction
from django.conf import settings

import subprocess
from django.http import HttpRequest, HttpResponse, QueryDict
from docx2pdf import convert  # You can use docx2pdf to convert HTML to PDF

# import pypandoc
from django.template import Context
from django.template.loader import get_template

# PDF GENERATION ===================================================

# class GenerateConceptPlan(APIView):
#     def generate_pdf(req):


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


class GenerateProjectDocument(APIView):
    # pypandoc.convert_text(
    #                 filled_template, "pdf", format="latex", outputfile=pdf_file
    #             )

    def get_concept_plan(self, pk):
        try:
            obj = ConceptPlan.objects.filter(document=pk).first()
        except ConceptPlan.DoesNotExist:
            raise NotFound
        return obj

    def get_project_plan(self, pk):
        try:
            obj = ProjectPlan.objects.filter(document=pk).first()
        except ProjectPlan.DoesNotExist:
            raise NotFound
        return obj

    def get_progress_report(self, pk):
        try:
            obj = ProgressReport.objects.filter(document=pk).first()
        except ProgressReport.DoesNotExist:
            raise NotFound
        return obj

    def get_student_report(self, pk):
        try:
            obj = StudentReport.objects.filter(document=pk).first()
        except StudentReport.DoesNotExist:
            raise NotFound
        return obj

    def get_project_closure(self, pk):
        try:
            obj = ProjectClosure.objects.filter(document=pk).first()
        except ProjectClosure.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        kind = req.data["kind"]
        settings.LOGGER.info(
            msg=f"{req.user} is trying to generate pdf for doc id: {pk}"
        )
        if kind == "conceptplan":
            try:
                cp = self.get_concept_plan(pk=pk)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise ValueError("Error in Finding Concept Plan")
            # Perform latex pdf generation for Concept Plan
            return Response(status=HTTP_200_OK, data=ConceptPlanSerializer(cp).data)
        elif kind == "projectplan":
            try:
                pp = self.get_project_plan(pk=pk)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise ValueError("Error in Finding Project Plan")
            # Perform latex pdf generation for progress report
            return Response(status=HTTP_200_OK, data=ProjectPlanSerializer(pp).data)
        elif kind == "progressreport":
            try:
                pr = self.get_progress_report(pk=pk)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise ValueError("Error in Finding Progress Report")
        elif kind == "progressreport":
            # Define the LaTeX template content with placeholders
            template_path = os.path.join(
                settings.BASE_DIR, "documents", "latex_templates", "progressreport.tex"
            )

            with open(template_path, "r") as template_file:
                latex_template = template_file.read()
                # latex_template = latex_template.replace("{", "{{").replace("}", "}}")

            filled_template = latex_template

            # Create a dictionary with placeholders and their corresponding data
            # data = {
            #     "title": pypandoc.convert_text(
            #         pr.document.project.title, "tex", format="html"
            #     ),
            #     "aims_html_data": pypandoc.convert_text(pr.aims, "tex", format="html"),
            #     "context_html_data": pypandoc.convert_text(
            #         pr.context, "tex", format="html"
            #     ),
            #     "future_html_data": pypandoc.convert_text(
            #         pr.future, "tex", format="html"
            #     ),
            #     "implications_html_data": pypandoc.convert_text(
            #         pr.implications, "tex", format="html"
            #     ),
            #     "progress_html_data": pypandoc.convert_text(
            #         pr.progress, "tex", format="html"
            #     ),
            # }

            # Populate the LaTeX template with data
            # filled_template = latex_template.format(**data)
            # print(filled_template)

            for key, value in data.items():
                # Use the key (placeholder) and value (data) to replace the placeholders in the template
                filled_template = filled_template.replace("{{" + key + "}}", value)

            # Define the PDF file path
            pdf_file = os.path.join(
                settings.BASE_DIR,
                "documents",
                "latex_output",
                f"progress_report_{pk}.pdf",
            )

            # Create a dictionary with the task arguments and keyword arguments
            task_args = {
                # "data": filled_template,
                "data": filled_template,
                "pdf_file": pdf_file,
            }

            print(filled_template)

            def generate_pdf(data, pdf_file):
                # Perform the PDF generation as before
                print("gen")
                # pypandoc.convert_text(
                #     data,
                #     "pdf",
                #     format="latex",
                #     outputfile=pdf_file,
                #     extra_args=["--pdf-engine=pdflatex"],
                # )

            generate_pdf(**task_args)

            # generate_pdf.apply_async(kwargs=task_args)
            return Response({"message": "PDF generation started."})

            # Convert LaTeX content to PDF using pypandoc with an output file
            # pypandoc.convert_text(
            #     filled_template, "pdf", format="latex", outputfile=pdf_file
            # )

            # # Prepare the response with the generated PDF content
            # response = HttpResponse(content_type="application/pdf")
            # response[
            #     "Content-Disposition"
            # ] = 'attachment; filename="progress_report.pdf"'

            # with open(pdf_file, "rb") as pdf_content:
            #     response.write(pdf_content)

            # return response

            # return Response(status=HTTP_200_OK, data=ProgressReportSerializer(pr).data)
        elif kind == "studentreport":
            try:
                sr = self.get_student_report(pk=pk)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise ValueError("Error in Finding Student Report")
            # Perform latex pdf generation for student report  then return
            return Response(status=HTTP_200_OK, data=StudentReportSerializer(sr).data)

        elif kind == "projectclosure":
            try:
                pc = self.get_project_closure(pk=pk)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise ValueError("Error in Finding Project Closure")
            # Perform latex pdf generation for progress closure then return
            return Response(status=HTTP_200_OK, data=StudentReportSerializer(pc).data)


# REPORTS ==========================================================


class DownloadAnnualReport(APIView):
    def get(self, req):
        settings.LOGGER.error(msg=f"{req.user} is downloading annual report")
        pass


class Reports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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

        settings.LOGGER.error(msg=f"{user} is BATCH Creating PROGRESS/STUDENT reports for eligible projects")
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
            "dm": "",
            "publications": "",
            "research_intro": "",
            "service_delivery_intro": "",
            "student_intro": "",
            "creator": creator,
            "modifier": modifier,
        }

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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

        delete_reports(report)
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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class GetWithPDFs(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        reports_with_pdfs = AnnualReport.objects.exclude(pdf__isnull=True)

        # if reports_with_pdfs:
        serializer = TinyAnnualReportSerializer(
            reports_with_pdfs,
            context={"request": request},
            many=True,
        )
        return Response(serializer.data, status=HTTP_200_OK)
        # else:
        #     return None


class GetCompletedReports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


# PROJECT DOCUMENTS ==============================================


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
                # return Response(
                #     TinyProjectDocumentSerializer(project_document).data,
                #     status=HTTP_201_CREATED,
                # )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProjectDocuments(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        settings.LOGGER.info(msg=f"{req.user} is Creating Project Document for project {req.data.get('project')}")
        kind = req.data.get("kind")
        project_pk = req.data.get("project")
        document_serializer = ProjectDocumentCreateSerializer(
            data={
                "old_id": 1,
                "kind": kind,
                "status": "new",
                "project": project_pk,
                "creator": req.user.pk,
                "modifier": req.user.pk,
            }
        )

        if document_serializer.is_valid():
            with transaction.atomic():
                doc = document_serializer.save()
                if kind == "concept":
                    project = req.data.get("project")
                    concept_plan_data_object = {
                        "document": doc.pk,
                        "project": project,
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
                        "staff_time_allocation": req.data.get("staff_time_allocation")
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
        </table>',
                        "budget": req.data.get("budget")
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
    </table>',
                    }

                    concept_plan_serializer = ConceptPlanCreateSerializer(
                        data=concept_plan_data_object
                    )
                    if concept_plan_serializer.is_valid():
                        # with transaction.atomic():
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
                        "background": req.data.get("background")
                        if req.data.get("background") is not None
                        else "<p></p>",
                        "methodology": req.data.get("methodology")
                        if req.data.get("methodology") is not None
                        else "<p></p>",
                        "aims": req.data.get("aims")
                        if req.data.get("aims") is not None
                        else "<p></p>",
                        "outcome": req.data.get("outcome")
                        if req.data.get("outcome") is not None
                        else "<p></p>",
                        "knowledge_transfer": req.data.get("knowledge_transfer")
                        if req.data.get("knowledge_transfer") is not None
                        else "<p></p>",
                        "listed_references": req.data.get("listed_references")
                        if req.data.get("listed_references") is not None
                        else "<p></p>",
                        "operating_budget": req.data.get("operating_budget")
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
        </table>',
                        "operating_budget_external": req.data.get(
                            "operating_budget_external"
                        )
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
        </table>',
                        "related_projects": req.data.get("related_projects")
                        if req.data.get("related_projects") is not None
                        else "<p></p>",
                    }
                    project_plan_serializer = ProjectPlanCreateSerializer(
                        data=project_plan_data_object
                    )

                    if project_plan_serializer.is_valid():
                        # with transaction.atomic():
                        try:
                            projplan = project_plan_serializer.save()
                            endorsements = EndorsementCreationSerializer(
                                data={
                                    "project_plan": projplan.pk,
                                    "bm_endorsement_required": True,
                                    "hc_endorsement_required": False,
                                    # "dm_endorsement_required": True,
                                    "ae_endorsement_required": False,
                                    "bm_endorsement_provided": False,
                                    "hc_endorsement_provided": False,
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
                        "scientific_outputs": req.data.get("scientific_outputs")
                        if req.data.get("scientific_outputs") is not None
                        else "<p></p>",
                        "knowledge_transfer": req.data.get("knowledge_transfer")
                        if req.data.get("knowledge_transfer") is not None
                        else "<p></p>",
                        "data_location": req.data.get("data_location")
                        if req.data.get("data_location") is not None
                        else "<p></p>",
                        "hardcopy_location": req.data.get("hardcopy_location")
                        if req.data.get("hardcopy_location") is not None
                        else "<p></p>",
                        "backup_location": req.data.get("backup_location")
                        if req.data.get("backup_location") is not None
                        else "<p></p>",
                    }

                    closure_serializer = ProjectClosureCreationSerializer(
                        data=closure_data_object
                    )

                    if closure_serializer.is_valid():
                        try:
                            with transaction.atomic():
                                closure = closure_serializer.save()
                                closure.document.project.status = "closure_requested"
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

                    progress_report_data_object = {
                        "document": doc.pk,
                        "report": report_id,
                        "project": project,
                        "year": year,
                        "context": req.data.get("context")
                        if req.data.get("context") is not None
                        else "<p></p>",
                        "implications": req.data.get("implications")
                        if req.data.get("implications") is not None
                        else "<p></p>",
                        "future": req.data.get("future")
                        if req.data.get("future") is not None
                        else "<p></p>",
                        "progress": req.data.get("progress")
                        if req.data.get("progress") is not None
                        else "<p></p>",
                        "aims": req.data.get("aims")
                        if req.data.get("aims") is not None
                        else "<p></p>",
                        "is_final_report": req.data.get("is_final_report")
                        if req.data.get("is_final_report") is not None
                        else False,
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

                    student_report_data_object = {
                        "document": doc.pk,
                        "report": report.pk,
                        "project": project,
                        "year": report.year,
                        "progress_report": req.data.get("progress_report")
                        if req.data.get("progress_report") is not None
                        else "<p></p>",
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


# class ProjectDocsPendingApproval(APIView):
#     permission_classes = [IsAuthenticatedOrReadOnly]

#     def get(self, req):
#         all_docs_pending_approval = ProjectDocument.objects.filter(
#             status=ProjectDocument.StatusChoices.INAPPROVAL,
#             business_area_lead_approval_granted=True,
#         ).all()
#         ser = TinyProjectDocumentSerializer(
#             all_docs_pending_approval,
#             many=True,
#             context={"request": req},
#         )
#         return Response(
#             ser.data,
#             status=HTTP_200_OK,
#         )


class EndorsementsPendingMyAction(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting endorsements pending action")
        is_bio = req.user.is_biometrician
        is_hc = req.user.is_herbarium_curator
        is_aec = req.user.is_aec
        is_superuser = req.user.is_superuser

        documents = []
        aec_input_required = []
        bm_input_required = []
        hc_input_required = []

        if is_bio or is_superuser or is_aec or is_hc:
            active_projects = Project.objects.exclude(status=Project.ACTIVE_ONLY).all()

            for project in active_projects:
                project_docs = ProjectDocument.objects.filter(
                    project=project,
                    kind=ProjectDocument.CategoryKindChoices.PROJECTPLAN,
                ).all()
                for doc in project_docs:
                    # find the related project plan
                    project_plan = ProjectPlan.objects.filter(document=doc).first()
                    endorsements = Endorsement.objects.get(project_plan=project_plan)
                    if (
                        (is_bio or is_superuser)
                        and (endorsements.bm_endorsement_required)
                        and not (endorsements.bm_endorsement_provided)
                    ):
                        documents.append(doc)
                        bm_input_required.append(doc)
                    if (
                        (is_aec or is_superuser)
                        and (endorsements.ae_endorsement_required)
                        and not (endorsements.ae_endorsement_provided)
                    ):
                        documents.append(doc)
                        aec_input_required.append(doc)
                    if (
                        (is_hc or is_superuser)
                        and (endorsements.hc_endorsement_required)
                        and not (endorsements.hc_endorsement_provided)
                    ):
                        documents.append(doc)
                        hc_input_required.append(doc)


        filtered_aec_input_required = list(
            {doc.id: doc for doc in aec_input_required}.values()
        )
        filtered_bm_input_required = list(
            {doc.id: doc for doc in bm_input_required}.values()
        )
        filtered_hc_input_required = list(
            {doc.id: doc for doc in hc_input_required}.values()
        )

        data = {
            "aec": TinyProjectDocumentSerializer(
                filtered_aec_input_required,
                many=True,
                context={"request": req},
            ).data,
            "bm": TinyProjectDocumentSerializer(
                filtered_bm_input_required,
                many=True,
                context={"request": req},
            ).data,
            "hc": TinyProjectDocumentSerializer(
                filtered_hc_input_required,
                many=True,
                context={"request": req},
            ).data,
        }

        return Response(
            data,
            status=HTTP_200_OK,
        )


class ProjectDocsPendingMyActionStageOne(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting docs pending stage 2 action")
        ba_input_required = []

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
                            ba_input_required.append(doc)
            else:
                filename = "activeProjectsWithoutBAs.txt"

                # Read existing content from the file
                with open(filename, "r") as file:
                    existing_content = file.read()
                # Check if the content already exists
                if f"{project.pk} | {project.title}\n" not in existing_content:
                    # Append to the file
                    with open(filename, "a") as file:
                        file.write(f"{project.pk} | {project.title}\n")

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
                filename = "activeProjectsWithoutBAs.txt"

                # Read existing content from the file
                with open(filename, "r") as file:
                    existing_content = file.read()
                # Check if the content already exists
                if f"{project.pk} | {project.title}\n" not in existing_content:
                    # Append to the file
                    with open(filename, "a") as file:
                        file.write(f"{project.pk} | {project.title}\n")
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is getting their documents pending action"
        )
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
                filename = "activeProjectsWithoutBAs.txt"

                # Read existing content from the file
                with open(filename, "r") as file:
                    existing_content = file.read()
                # Check if the content already exists
                if f"{project.pk} | {project.title}\n" not in existing_content:
                    # Append to the file
                    with open(filename, "a") as file:
                        file.write(f"{project.pk} | {project.title}\n")

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


class ProjectDocumentDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ProjectDocumentComments(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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

    def post(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is trying to post a comment to doc {pk}")
        ser = TinyCommentCreateSerializer(
            data={
                "document": pk,
                "text": req.data["payload"],
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


class ConceptPlans(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ProjectPlans(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ProgressReports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class StudentReports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ProjectClosures(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ConceptPlanDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
            u_concept_plan.document.updated_at = datetime.datetime.now()
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


class ProjectPlanDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
            msg=f"{req.user} is updating project plan details for {pk}"
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


class ProgressReportByYear(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, project, year):
        try:
            obj = ProgressReport.objects.get(year=year, document__project=project)
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


class StudentReportByYear(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ProgressReportDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class StudentReportDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class ProjectClosureDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class RepoenProject(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_project(self, pk):
    #     try:
    #         obj = Project.objects.get(pk=pk)
    # #     except Project.DoesNotExist:
    #         raise NotFound
    #     return obj

    def get_base_document(self, project_pk):
        try:
            obj = ProjectDocument.objects.get(project=project_pk, kind="projectclosure")
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    # def get_closure(self, project_pk):
    #     try:
    #         obj = ProjectClosure.objects.get(pr=project_pk)
    #     except ProjectClosure.DoesNotExist:
    #         raise NotFound
    #     return obj

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is reopening project belonging to doc ({pk})"
        )
        with transaction.atomic():
            try:
                settings.LOGGER.info(msg=f"{req.user} is reopening project {pk}")
                project_document = self.get_base_document(pk)
                project_document.project.status = "updating"
                project_document.project.save()
                project_document.delete()
                return Response(status=HTTP_204_NO_CONTENT)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                return Response(f"{e}", status=HTTP_400_BAD_REQUEST)


# ENDORSEMENTS & APPROVALS ==========================================================


class DocReopenProject(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_document(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is reopening project by deleting closure")
        user = req.user
        settings.LOGGER.info(
            msg=f"{req.user} is reopening project {req.data['documentPk']}"
        )
        stage = req.data["stage"]
        document_pk = req.data["documentPk"]
        if not stage and not document_pk:
            settings.LOGGER.error(msg=f"Error reopening - no stage/doc pk")
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
        project = document.project
        project.status = "updating"
        project.save()
        closure = ProjectClosure.objects.get(document=document)
        closure.delete()
        document.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class DocApproval(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_document(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        user = req.user
        stage = req.data["stage"]
        document_pk = req.data["documentPk"]
        settings.LOGGER.info(msg=f"{req.user} is approving a doc {document_pk}")
        if not stage and not document_pk:
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
        settings.LOGGER.info(msg=f"{req.user} is approving {document}")
        if int(stage) == 1:
            data = {
                "project_lead_approval_granted": True,
                "modifier": req.user.pk,
                "status": "inapproval",
            }
        elif int(stage) == 2:
            data = {
                "business_area_lead_approval_granted": True,
                "modifier": req.user.pk,
                "status": "inapproval",
            }
        elif int(stage) == 3:
            data = {
                "directorate_approval_granted": True,
                "modifier": req.user.pk,
                "status": "approved",
            }
        else:
            settings.LOGGER.error(msg=f"No stage provided for approval")
            return Response(
                status=HTTP_400_BAD_REQUEST,
            )
        ser = ProjectDocumentSerializer(
            document,
            data=data,
            partial=True,
        )
        if ser.is_valid():
            u_document = ser.save()
            if u_document.kind == "projectplan" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.ACTIVE
                u_document.project.save()
            if u_document.kind == "projectclosure" and (stage == 3 or stage == "3"):
                settings.LOGGER.info(msg=f"{req.user} is closing a project")
                # find the closure matching
                closure_doc = ProjectClosure.objects.get(document=u_document)
                outcome = closure_doc.intended_outcome
                if outcome == "forcecompleted":
                    outcome = "completed"
                u_document.project.status = outcome
                u_document.project.save()

            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DocRecall(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_document(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        user = req.user
        stage = req.data["stage"]
        document_pk = req.data["documentPk"]
        settings.LOGGER.info(msg=f"{req.user} is recalling a doc {document_pk}")
        if not stage and not document_pk:
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
        settings.LOGGER.info(msg=f"{req.user} is recalling {document}")

        data = "test"
        if int(stage) == 1:
            if document.business_area_lead_approval_granted == False:
                data = {
                    "project_lead_approval_granted": False,
                    "modifier": req.user.pk,
                    "status": "revising",
                }

        elif int(stage) == 2:
            if document.directorate_approval_granted == False:
                data = {
                    "business_area_lead_approval_granted": False,
                    "modifier": req.user.pk,
                    "status": "inapproval",
                }
        elif int(stage) == 3:
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
            if u_document.kind == "projectplan" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.PENDING
                u_document.project.save()
            elif u_document.kind == "projectclosure" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.CLOSUREREQ
                u_document.project.save()

            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DocSendBack(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_document(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        user = req.user
        stage = req.data["stage"]
        document_pk = req.data["documentPk"]
        settings.LOGGER.info(msg=f"{req.user} is sending back a doc {document_pk}")
        if not stage and not document_pk:
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
        settings.LOGGER.info(msg=f"{req.user} is sending back {document}")
        data = "test"
        if int(stage) == 2:
            if document.directorate_approval_granted == False:
                data = {
                    "business_area_lead_approval_granted": False,
                    "project_lead_approval_granted": False,
                    "modifier": req.user.pk,
                    "status": "revising",
                }
        elif int(stage) == 3:
            data = {
                "business_area_lead_approval_granted": False,
                "directorate_approval_granted": False,
                "modifier": req.user.pk,
                "status": "revising",
            }

        ser = ProjectDocumentSerializer(
            document,
            data=data,
            partial=True,
        )
        if ser.is_valid():
            u_document = ser.save()
            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class Endorsements(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class SeekEndorsement(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
                            "endorsement": updated.id,  # Assuming 'endorsement' is a ForeignKey
                            "creator": req.user.id,  # Assuming 'creator' is a ForeignKey
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


class EndorsementDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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


# PUBLICATIONS ==========================================================


class Publications(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all_publications = Publication.objects.all()
        ser = TinyPublicationSerializer(
            all_publications,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.error(msg=f"{req.user} is posting a publication")
        ser = PublicationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            new_publication = ser.save()
            return Response(
                TinyPublicationSerializer(new_publication).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class PublicationDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = Publication.objects.get(pk=pk)
        except Publication.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        publication = self.go(pk)
        ser = PublicationSerializer(
            publication,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    # Commented out as accidentally deleting vai drf would cause errors (non-existent endorsements on frontend)
    def delete(self, req, pk):
        settings.LOGGER.error(msg=f"{req.user} is deleting publication {pk}")
        publication = self.go(pk)
        publication.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        settings.LOGGER.error(msg=f"{req.user} is updating publication {pk}")
        publication = self.go(pk)
        ser = PublicationSerializer(
            publication,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_publication = ser.save()
            return Response(
                TinyPublicationSerializer(u_publication).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )
