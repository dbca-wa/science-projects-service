from django.shortcuts import render
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
    EndorsementSerializer,
    ProgressReportSerializer,
    ProjectClosureSerializer,
    ProjectDocumentSerializer,
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
        ser = AnnualReportSerializer(
            data=req.data,
        )
        if ser.is_valid():
            report = ser.save()
            return Response(
                TinyAnnualReportSerializer(report).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
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
        ser = ProjectDocumentSerializer(
            data=req.data,
        )
        if ser.is_valid():
            project_document = ser.save()
            return Response(
                TinyProjectDocumentSerializer(project_document).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
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


# ENDORSEMENTS ==========================================================


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
