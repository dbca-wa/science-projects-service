import datetime
import os
import time
from django.shortcuts import render

# from config.tasks import generate_pdf
from projects.models import Project, ProjectMember

from medias.models import AnnualReportPDF, ProjectDocumentPDF
from medias.serializers import (
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
from django.http import HttpResponse
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
        pdf = document.pdf
        print(pdf)
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
        print(req)
        kind = req.data["kind"]
        print(kind)

        if kind == "conceptplan":
            try:
                cp = self.get_concept_plan(pk=pk)
            except Exception as e:
                print(e)
                raise ValueError("Error in Finding Concept Plan")
            print(cp)
            # Perform latex pdf generation for Concept Plan
            return Response(status=HTTP_200_OK, data=ConceptPlanSerializer(cp).data)
        elif kind == "projectplan":
            try:
                pp = self.get_project_plan(pk=pk)
            except Exception as e:
                print(e)
                raise ValueError("Error in Finding Project Plan")
            print(pp)
            # Perform latex pdf generation for progress report
            return Response(status=HTTP_200_OK, data=ProjectPlanSerializer(pp).data)
        elif kind == "progressreport":
            try:
                pr = self.get_progress_report(pk=pk)
                print(pr)
            except Exception as e:
                print(e)
                raise ValueError("Error in Finding Progress Report")

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
                print(e)
                raise ValueError("Error in Finding Student Report")
            print(sr)
            # Perform latex pdf generation for student report  then return
            return Response(status=HTTP_200_OK, data=StudentReportSerializer(sr).data)

        elif kind == "projectclosure":
            try:
                pc = self.get_project_closure(pk=pk)
            except Exception as e:
                print(e)
                raise ValueError("Error in Finding Project Closure")
            print(pc)
            # Perform latex pdf generation for progress closure then return
            return Response(status=HTTP_200_OK, data=StudentReportSerializer(pc).data)

        # project_document = self.get_proj_document(pk)
        # if project_document.kind == "progressreport":
        #     progress_report = self.get_progress_report(pk=pk)
        #     print(progress_report)
        #     # project = self.get_project(project_document.project.pk)
        #     for field in progress_report._meta.fields:
        #         field_name = field.name
        #         field_value = getattr(progress_report, field_name)
        #         print(f"{field_name}: {field_value}")

        # print(project_document)
        # for field in project_document._meta.fields:
        #     field_name = field.name
        #     field_value = getattr(project_document, field_name)
        #     print(f"{field_name}: {field_value}")

        # if project_document.kind == "progressreport":
        #     # get the specific project document
        #     specific_document = project_document.progress_report_details
        #     print(specific_document)
        #     print

        # try:
        #     document = ProjectDocumentPDF.objects.get(document__pk=pk)
        # except ProjectDocumentPDF.DoesNotExist:
        #     # If the document doesn't exist, create a new instance
        #     document_data = {
        #         "project": req.data["project_pk"],
        #         "document": req.data["document_pk"],
        #         # "file": req.data["file"],
        #     }
        #     document = ProjectDocumentPDF(**document_data)

        # ser = ProjectDocumentPDFSerializer(document)
        # if ser.is_valid():
        #     print("serializer valid")
        #     ser = ser.save()
        #     return Response(
        #         ser.data,
        #         status=HTTP_200_OK,
        #     )
        # else:
        #     print("serializer invalid")
        #     return Response(
        #         ser.errors,
        #         status=HTTP_400_BAD_REQUEST,
        #     )
        # document.save()  # Save the newly created instance to the database

        #             {
        #         "project": 7,
        #         "old_file": "",
        #         "document": 2135,
        #         "file": "https://scienceprojects.dbca.wa.gov.au/media/ararreports/12/AnnualReport20222023_25.pdf"
        # }
        # if document.pdf_generation_in_progress:
        #     return Response(
        #         data="A PDF file is already being generate, please wait",
        #         status=HTTP_403_FORBIDDEN,
        #     )

        # document.pdf_generation_in_progress = True

        # document.pdf_generation_in_progress = True


# REPORTS ==========================================================


class DownloadAnnualReport(APIView):
    def get(self, req):
        pass
        # try:
        #     # Retrieve projects data from the database
        #     core_projects = CoreFunctionProject.objects.all()

        #     # Create a response object with CSV content type
        #     res = HttpResponse(content_type="text/csv")
        #     res["Content-Disposition"] = 'attachment; filename="projects.csv"'

        #     # Create a CSV writer
        #     writer = csv.writer(res)
        #     writer.writerow(["-----", "Core Function Projects", "-----"])

        #     # Get field names (CoreFunctionProject)
        #     core_field_names = [
        #         field.name for field in CoreFunctionProject._meta.fields
        #     ]

        #     # Write CSV headers (CoreFunctionProject)
        #     writer.writerow(core_field_names)
        #     # print(res.data)

        #     # Write project data rows
        #     for project in core_projects:
        #         row = [getattr(project, field) for field in core_field_names]
        #         writer.writerow(row)

        #     # Add an empty row for separation
        #     writer.writerow([])
        #     writer.writerow(["-----", "Science Projects", "-----"])

        #     science_projects = ScienceProject.objects.all()

        #     # Get field names (ScienceProject)
        #     science_field_names = [field.name for field in ScienceProject._meta.fields]

        #     # Write CSV headers for (Science Project)
        #     writer.writerow(science_field_names)

        #     # Write project data rows
        #     for project in science_projects:
        #         row = [getattr(project, field) for field in science_field_names]
        #         writer.writerow(row)

        #     # Add an empty row for separation
        #     writer.writerow([])
        #     writer.writerow(["-----", "Student Projects", "-----"])

        #     student_projects = StudentProject.objects.all()

        #     # Get field names (StudentProject)
        #     student_field_names = [field.name for field in StudentProject._meta.fields]

        #     # Write CSV headers (StudentProject)
        #     writer.writerow(student_field_names)

        #     # Write project data rows
        #     for project in student_projects:
        #         row = [getattr(project, field) for field in student_field_names]
        #         writer.writerow(row)

        #     # Add an empty row for separation
        #     writer.writerow([])
        #     writer.writerow(["-----", "External Projects", "-----"])

        #     external_projects = ExternalProject.objects.all()

        #     # Get field names (ExternalProject)
        #     external_field_names = [
        #         field.name for field in ExternalProject._meta.fields
        #     ]

        #     # Write CSV headers (StudentProject)
        #     writer.writerow(external_field_names)

        #     # Write project data rows
        #     for project in external_projects:
        #         row = [getattr(project, field) for field in external_field_names]
        #         writer.writerow(row)

        #     return res

        # # If server is down or otherwise error
        # except Exception as e:
        #     print(e)
        #     return HttpResponse(status=500, content="Error generating CSV")


class Reports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
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

        print("Fetching eligible project")
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
        print("Fetched eligible project")

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

            print("Serializing document")

            new_project_document = ProjectDocumentCreateSerializer(data=new_doc_data)
            print("Serialized document")

            if new_project_document.is_valid():
                with transaction.atomic():
                    print("Saving document")
                    doc = new_project_document.save()
                    print("Saved document")
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
                        print("Serializing PR")

                        progress_report = ProgressReportCreateSerializer(
                            data=progress_report_data
                        )
                        print("Serialized PR")

                        if progress_report.is_valid():
                            print("Saving PR")
                            progress_report.save()
                            print("Saved PR")
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                        else:
                            print(
                                "ERROR IN PROGRESS REPORT SERIALIZER",
                                progress_report.errors,
                            )
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
                        print("Serializing SR")

                        progress_report = StudentReportCreateSerializer(
                            data=student_report_data
                        )
                        print("Serialized SR")

                        if progress_report.is_valid():
                            print("Saving SPR")
                            progress_report.save()
                            print("Saved SPR")
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                        else:
                            print(
                                "ERROR IN PROGRESS REPORT SERIALIZER",
                                progress_report.errors,
                            )
                            return Response(
                                progress_report.errors, HTTP_400_BAD_REQUEST
                            )

            else:
                print("ERROR IN DOC SERIALIZER", new_project_document.errors)
                return Response(new_project_document.errors, HTTP_400_BAD_REQUEST)

    def post(self, req):
        print(req.data)
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

        print("serializing report")

        ser = AnnualReportSerializer(
            data={**creation_data},
        )
        if ser.is_valid():
            print("report serializer valid")
            with transaction.atomic():
                print("saving report")

                report = ser.save()
                print("report saved")
                should_seek_reports_now = req.data.get("seek_update")
                if should_seek_reports_now == True:
                    try:
                        print("attempting pr creation for eligible")
                        self.create_reports_for_eligible_projects(
                            report_id=report.id, user=req.user
                        )
                    except Exception as e:
                        print("failed creation of eligible")
                        print(e)
                        return Response(
                            e,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyAnnualReportSerializer(report).data,
                    status=HTTP_201_CREATED,
                )
        else:
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
        if ser.is_valid():
            with transaction.atomic():
                try:
                    print("jere")
                    project_document = ser.save()
                    print("ser saved")
                except Exception as e:
                    print(e)
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
        print(req.data)
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
            print("\n\nvalid\n\n")
            print("Serializer for doc is good")
            # print(document_serializer.data)
            # doc = document_serializer.save()
            with transaction.atomic():
                print("saving doc")
                doc = document_serializer.save()
                print("saved doc")
                if kind == "concept":
                    print("kind concept")
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
                        else "<p></p>",
                        "budget": req.data.get("budget")
                        if req.data.get("budget") is not None
                        else "<p></p>",
                    }
                    print("concept Plan serializing")

                    concept_plan_serializer = ConceptPlanCreateSerializer(
                        data=concept_plan_data_object
                    )
                    print("concept Plan serialized")
                    if concept_plan_serializer.is_valid():
                        print("concept plan valid")
                        # with transaction.atomic():
                        try:
                            concplan = concept_plan_serializer.save()
                            print("saved")
                        except Exception as e:
                            print(f"concept Plan error: {e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        print("concept Plan error heree")
                        print(project_plan_serializer.errors)
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
                        # "involves_plants": req.data.get("involves_plants")
                        # if req.data.get("involves_plants") is not None
                        # else False,
                        # "involves_animals": req.data.get("involves_animals")
                        # if req.data.get("involves_animals") is not None
                        # else False,
                        "operating_budget": req.data.get("operating_budget")
                        if req.data.get("operating_budget") is not None
                        else "<p></p>",
                        "operating_budget_external": req.data.get(
                            "operating_budget_external"
                        )
                        if req.data.get("operating_budget_external") is not None
                        else "<p></p>",
                        "related_projects": req.data.get("related_projects")
                        if req.data.get("related_projects") is not None
                        else "<p></p>",
                    }
                    print(project_plan_data_object)
                    project_plan_serializer = ProjectPlanCreateSerializer(
                        data=project_plan_data_object
                    )

                    if project_plan_serializer.is_valid():
                        print("project plan valid")
                        # with transaction.atomic():
                        try:
                            projplan = project_plan_serializer.save()
                            print("saved")
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
                                print("saving endorsement...")
                                endorsements.save()
                                print("saved")

                            else:
                                print(f"endorsement error: {endorsements.errors}")
                                return Response(
                                    endorsements.errors,
                                    HTTP_400_BAD_REQUEST,
                                )

                        except Exception as e:
                            print(f"project Plan error: {e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        print("project Plan")
                        print(project_plan_serializer.errors)
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
                        print("closure valid")
                        try:
                            with transaction.atomic():
                                closure = closure_serializer.save()
                                closure.document.project.status = outcome
                                print("saving project")
                                closure.document.project.save()
                                print("project saved")

                        except Exception as e:
                            print(f"Closure save error: {e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        print("Closure Error")
                        print(closure_serializer.errors)
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
                        print("progress report valid")
                        try:
                            with transaction.atomic():
                                progress_report = pr_serializer.save()
                                progress_report.document.project.status = "updating"
                                print("saving project")
                                progress_report.document.project.save()
                                print("project saved")

                        except Exception as e:
                            print(f"Progress Report save error: {e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        print("Progress Report Error")
                        print(pr_serializer.errors)
                        return Response(
                            pr_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                elif kind == "studentreport":
                    print("Kind is Student")

                    project = req.data.get("project")
                    report_id = req.data.get("report")
                    print("getting report...")
                    report = AnnualReport.objects.get(pk=report_id)
                    print("got report...", report)

                    student_report_data_object = {
                        "document": doc.pk,
                        "report": report.pk,
                        "project": project,
                        "year": report.year,
                        "progress_report": req.data.get("progress_report")
                        if req.data.get("progress_report") is not None
                        else "<p></p>",
                    }
                    print("DATA:")
                    print(student_report_data_object)
                    print("Serializing...")
                    sr_serializer = StudentReportCreateSerializer(
                        data=student_report_data_object
                    )

                    if sr_serializer.is_valid():
                        print("Student report valid")
                        try:
                            with transaction.atomic():
                                print("saving student serializer...")
                                student_report = sr_serializer.save()
                                print("student serializer saved...")
                                student_report.document.project.status = "updating"
                                print("saving project")
                                student_report.document.project.save()
                                print("project saved")

                        except Exception as e:
                            print(f"Student Report save error: {e}")
                            return Response(
                                e,
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        print("Student Report Error")
                        print(sr_serializer.errors)
                        return Response(
                            sr_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyProjectDocumentSerializer(doc).data,
                    status=HTTP_201_CREATED,
                )
        else:
            print("Main Doc Serializer issue")
            print(document_serializer.errors)
            return Response(
                document_serializer.errors,
                HTTP_400_BAD_REQUEST,
            )


class ProjectDocsPendingApproval(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all_docs_pending_approval = ProjectDocument.objects.filter(
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            business_area_lead_approval_granted=True,
        ).all()
        ser = TinyProjectDocumentSerializer(
            all_docs_pending_approval,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class ProjectDocsPendingMyAction(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        documents = []
        pm_bl_input_required = []
        ba_input_required = []
        directorate_input_required = []
        aec_input_required = []
        bm_input_required = []
        hc_input_required = []

        user_work = UserWork.objects.get(user=req.user.pk)

        # Directorate flagging
        is_directorate = user_work.business_area.name == "Directorate"
        if is_directorate:
            active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY).all()

            for project in active_projects:
                project_docs = (
                    ProjectDocument.objects.filter(project=project)
                    .exclude(status=ProjectDocument.StatusChoices.APPROVED)
                    .all()
                )
                for doc in project_docs:
                    if (doc.business_area_lead_approval_granted == True) and (
                        doc.directorate_approval_granted == False
                    ):
                        documents.append(doc)
                        directorate_input_required.append(doc)

        # Business Area Lead Flagging
        is_business_area_lead = user_work.business_area.leader == req.user
        if is_business_area_lead:
            active_projects_in_ba = (
                Project.objects.filter(business_area=user_work.business_area)
                .exclude(status=Project.CLOSED_ONLY)
                .all()
            )

            for project in active_projects_in_ba:
                project_docs = (
                    ProjectDocument.objects.filter(project=project)
                    .exclude(status=ProjectDocument.StatusChoices.APPROVED)
                    .all()
                )
                for doc in project_docs:
                    if (doc.project_lead_approval_granted == True) and (
                        doc.business_area_lead_approval_granted == False
                    ):
                        documents.append(doc)
                        ba_input_required.append(doc)

        # Project Lead / Team Member Flagging
        # projects_where_leader = ProjectMember.objects.filter(is_leader=True, user=req.user).all()
        all_proj_pks_where_member = []
        project_membership = ProjectMember.objects.filter(user=req.user).all()
        for proj in project_membership:
            all_proj_pks_where_member.append(proj.project)
        for project in all_proj_pks_where_member:
            project_docs = (
                ProjectDocument.objects.filter(project=project)
                .exclude(status=ProjectDocument.StatusChoices.APPROVED)
                .all()
            )
            for doc in project_docs:
                if doc.project_lead_approval_granted == False:
                    documents.append(doc)
                    pm_bl_input_required.append(doc)

        is_bio = req.user.is_biometrician
        is_hc = req.user.is_herbarium_curator
        is_aec = req.user.is_aec
        is_superuser = req.user.is_superuser

        # 2) if user is bio, get all progress/student reports requiring that endorsement, but not marked as
        # actually endorsed
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
                        print("Doc found where bio required, but not yet granted")
                        print(doc)
                        documents.append(doc)
                        bm_input_required.append(doc)
                    if (
                        (is_aec or is_superuser)
                        and (endorsements.ae_endorsement_required)
                        and not (endorsements.ae_endorsement_provided)
                    ):
                        print("Doc found where aec required, but not yet granted")

                        print(doc)
                        documents.append(doc)
                        aec_input_required.append(doc)
                    if (
                        (is_hc or is_superuser)
                        and (endorsements.hc_endorsement_required)
                        and not (endorsements.hc_endorsement_provided)
                    ):
                        print("Doc found where hc required, but not yet granted")
                        print(doc)
                        documents.append(doc)
                        hc_input_required.append(doc)

        print(is_bio, is_hc, is_aec, is_superuser)

        # TODO: Instead return a set of arrays which have been filtered
        # pm_bl_input_required
        # ba_input_required
        # directorate_input_required
        # aec_input_required
        # bm_input_required
        # hc_input_required

        filtered_documents = list({doc.id: doc for doc in documents}.values())
        filtered_pm_bl_input_required = list(
            {doc.id: doc for doc in pm_bl_input_required}.values()
        )
        filtered_ba_input_required = list(
            {doc.id: doc for doc in ba_input_required}.values()
        )
        filtered_directorate_input_required = list(
            {doc.id: doc for doc in directorate_input_required}.values()
        )
        filtered_aec_input_required = list(
            {doc.id: doc for doc in aec_input_required}.values()
        )
        filtered_bm_input_required = list(
            {doc.id: doc for doc in bm_input_required}.values()
        )
        filtered_hc_input_required = list(
            {doc.id: doc for doc in hc_input_required}.values()
        )
        ser = TinyProjectDocumentSerializer(
            filtered_documents,
            many=True,
            context={"request": req},
        )

        data = {
            "all": ser.data,
            "team": TinyProjectDocumentSerializer(
                filtered_pm_bl_input_required,
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
        project_document.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        project_document = self.go(pk)
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
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


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
        if ser.is_valid():
            concept_plan = ser.save()
            return Response(
                TinyConceptPlanSerializer(concept_plan).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
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
        if ser.is_valid():
            project_plan = ser.save()
            return Response(
                TinyProjectPlanSerializer(project_plan).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
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
        if ser.is_valid():
            progress_report = ser.save()
            return Response(
                TinyProgressReportSerializer(progress_report).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
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
            return Response(
                HTTP_400_BAD_REQUEST,
            )


# For saving rich text


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
        concept_plan.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        concept_plan = self.go(pk)
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
        project_plan = self.go(pk)
        project_plan.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        print(req.data)
        if (
            "data_management" in req.data
            or "specimens" in req.data
            or "involves_animals" in req.data
            or "involves_plants" in req.data
        ):
            endorsement_to_edit = Endorsement.objects.filter(project_plan=pk).first()
            if "specimens" in req.data:
                specimen_value = req.data["specimens"]
                print(f"specimen value: {specimen_value}")
                endorsement_to_edit.no_specimens = specimen_value

            if "data_management" in req.data:
                data_management_value = req.data["data_management"]
                print(f"data_management value: {data_management_value}")
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
        progress_report.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        progress_report = self.go(pk)
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
        student_report.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        student_report = self.go(pk)
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
        if ser.is_valid():
            u_project_closure = ser.save()
            return Response(
                TinyProjectClosureSerializer(u_project_closure).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
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
        with transaction.atomic():
            try:
                project_document = self.get_base_document(pk)
                project_document.project.status = "updating"
                project_document.project.save()
                project_document.delete()
                return Response(status=HTTP_204_NO_CONTENT)
            except Exception as e:
                print(e)
                return Response(f"{e}", status=HTTP_400_BAD_REQUEST)


# ENDORSEMENTS & APPROVALS ==========================================================


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
        print(user, stage, document_pk)
        if not stage and not document_pk:
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
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
                print("weeeeeeeeeeeeeeeeeeeeeeeeeeeee")
                print(u_document.project.status)
                u_document.project.status = Project.StatusChoices.ACTIVE
                u_document.project.save()
                print(u_document.project.status)
            else:
                # if u_document.kind == "progressreport" or u_document.kind == "studentreport":
                #     if (stage == 2 or stage == '2'):

                # else:

                print("nope")
                print(u_document.kind)
                print(stage)

            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
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
        print(user, stage, document_pk)
        if not stage and not document_pk:
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
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
                    "status": "revising",
                }
        elif int(stage) == 3:
            data = {
                "directorate_approval_granted": False,
                "modifier": req.user.pk,
                "status": "revising",
            }

        if data == "test":
            return Response(status=HTTP_400_BAD_REQUEST)

        ser = ProjectDocumentSerializer(
            document,
            data=data,
            partial=True,
        )
        if ser.is_valid():
            u_document = ser.save()
            if u_document.kind == "projectplan" and (stage == 3 or stage == "3"):
                print("weeeeeeeeeeeeeeeeeeeeeeeeeeeee")
                print(u_document.project.status)
                u_document.project.status = Project.StatusChoices.PENDING
                u_document.project.save()
                print(u_document.project.status)
            else:
                print("nope")
                print(u_document.kind)
                print(stage)

            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            print(ser.errors)
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
        print(user, stage, document_pk)
        if not stage and not document_pk:
            return Response(status=HTTP_400_BAD_REQUEST)

        document = self.get_document(pk=document_pk)
        data = "test"
        if int(stage) == 2:
            if document.directorate_approval_granted == False:
                data = {
                    "business_area_lead_approval_granted": False,
                    "project_lead_approval_granted": False,
                    "modifier": req.user.pk,
                    "status": "inreview",
                }
        elif int(stage) == 3:
            data = {
                "business_area_lead_approval_granted": False,
                "directorate_approval_granted": False,
                "modifier": req.user.pk,
                "status": "inreview",
            }

        if data == "test":
            return Response(status=HTTP_400_BAD_REQUEST)

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
            return Response(
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

    # Commented out as accidentally deleting vai drf would cause errors (non-existent endorsements on frontend)
    # def delete(self, req, pk):
    #     endorsement = self.go(pk)
    #     endorsement.delete()
    #     return Response(
    #         status=HTTP_204_NO_CONTENT,
    #     )

    def put(self, req, pk):
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
        publication = self.go(pk)
        publication.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
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
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )
