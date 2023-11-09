import datetime
import os
import time
from django.shortcuts import render

# from config.tasks import generate_pdf
from projects.models import Project

from medias.models import ProjectDocumentPDF
from medias.serializers import ProjectDocumentPDFSerializer
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

from .serializers import (
    AnnualReportSerializer,
    ConceptPlanSerializer,
    EndorsementCreationSerializer,
    EndorsementSerializer,
    ProgressReportSerializer,
    ProjectClosureCreationSerializer,
    ProjectClosureSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
    ProjectPlanCreateSerializer,
    ProjectPlanSerializer,
    PublicationSerializer,
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

        ser = AnnualReportSerializer(
            data={**creation_data},
        )
        if ser.is_valid():
            report = ser.save()
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
        all_reports = AnnualReport.objects.all()
        if all_reports:
            latest_report = max(all_reports, key=lambda report: report.year)
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
                doc = document_serializer.save()
                if kind == "projectplan":
                    project_plan_data_object = {
                        "document": doc.pk,
                        "background": "<p></p>",
                        "methodology": "<p></p>",
                        "aims": "<p></p>",
                        "outcome": "<p></p>",
                        "knowledge_transfer": "<p></p>",
                        "listed_references": "<p></p>",
                        "involves_plants": False,
                        "involves_animals": False,
                        "operating_budget": "<p></p>",
                        "operating_budget_external": "<p></p>",
                        "related_projects": "<p></p>",
                    }
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
                                data={"project_plan": projplan.pk}
                            )
                            if endorsements.is_valid():
                                print("saving endorsement...")
                                endorsements.save()
                                print("saved")

                            else:
                                print(endorsements.errors)
                                return Response(
                                    endorsements.errors,
                                    HTTP_400_BAD_REQUEST,
                                )

                        except Exception as e:
                            print(f"project Plan error: {e}")
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

                    closure_data_object = {
                        "document": doc.pk,
                        "intended_outcome": outcome,
                        "reason": reason,
                        "scientific_outputs": "<p></p>",
                        "knowledge_transfer": "<p></p>",
                        "data_location": "<p></p>",
                        "hardcopy_location": "<p></p>",
                        "backup_location": "<p></p>",
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
                    else:
                        print("Closure Error")
                        print(closure_serializer.errors)
                        return Response(
                            closure_serializer.errors,
                            status=HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    TinyProjectDocumentSerializer(doc).data,
                    status=HTTP_201_CREATED,
                )
        else:
            print(document_serializer.errors)
            return Response(
                document_serializer.errors,
                HTTP_400_BAD_REQUEST,
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
