"""
Annual report views
"""

import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Max, Q
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView

from medias.models import AnnualReportPDF, LegacyAnnualReportPDF
from medias.serializers import (
    AnnualReportPDFSerializer,
    TinyLegacyAnnualReportPDFSerializer,
)

from ..models import AnnualReport, ProgressReport, StudentReport
from ..serializers import (
    AnnualReportSerializer,
    MiniAnnualReportSerializer,
    ProgressReportSerializer,
    StudentReportSerializer,
    TinyAnnualReportSerializer,
)


class Reports(APIView):
    """List and create annual reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List annual reports"""
        settings.LOGGER.info(f"{request.user} is viewing reports")
        all_reports = AnnualReport.objects.all()
        serializer = TinyAnnualReportSerializer(
            all_reports,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create annual report"""
        settings.LOGGER.info(f"{request.user} is creating a report")
        serializer = AnnualReportSerializer(data=request.data)

        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        report = serializer.save()
        return Response(
            TinyAnnualReportSerializer(report).data, status=HTTP_201_CREATED
        )


class ReportDetail(APIView):
    """Get, update, and delete annual reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get annual report by ID"""
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound

        serializer = AnnualReportSerializer(report, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update annual report"""
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound

        settings.LOGGER.info(f"{request.user} is updating report {report}")
        serializer = AnnualReportSerializer(
            report,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        updated_report = serializer.save()
        return Response(
            TinyAnnualReportSerializer(updated_report).data, status=HTTP_202_ACCEPTED
        )

    def delete(self, request, pk):
        """Delete annual report"""
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound

        settings.LOGGER.info(f"{request.user} is deleting report {report}")

        # Delete associated progress reports
        progress_reports = ProgressReport.objects.filter(report=report).all()
        for pr in progress_reports:
            pr.document.delete()

        # Delete associated student reports
        student_reports = StudentReport.objects.filter(report=report).all()
        for sr in student_reports:
            sr.document.delete()

        report.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class GetLatestReportYear(APIView):
    """Get the latest annual report year"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_year = AnnualReport.objects.aggregate(Max("year"))["year__max"]

        if latest_year is not None:
            latest_report = AnnualReport.objects.get(year=latest_year)
            serializer = AnnualReportSerializer(
                latest_report,
                context={"request": request},
            )
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            raise NotFound


class GetAvailableReportYearsForStudentReport(APIView):
    """Get available report years for student reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """
        Returns list of reports with year and ID.
        Only returns years where a student report doesn't already exist for the project.
        """
        if project_id:
            all_student_reports = StudentReport.objects.filter(
                document__project_id=project_id
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
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            raise NotFound


class GetAvailableReportYearsForProgressReport(APIView):
    """Get available report years for progress reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """
        Returns list of reports with year and ID.
        Only returns years where a progress report doesn't already exist for the project.
        """
        if project_id:
            all_progress_reports = ProgressReport.objects.filter(
                document__project_id=project_id
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
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            raise NotFound


class GetWithoutPDFs(APIView):
    """Get annual reports without PDFs"""

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
            return Response([], status=HTTP_200_OK)


class GetReportPDF(APIView):
    """Get annual report PDF"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            report_pdf_obj = AnnualReportPDF.objects.get(report=pk)
        except AnnualReportPDF.DoesNotExist:
            raise NotFound

        serializer = AnnualReportPDFSerializer(report_pdf_obj)

        # Convert serialized data to dictionary
        serialized_data = json.loads(json.dumps(serializer.data, cls=DjangoJSONEncoder))

        # Include PDF data in response
        serialized_data["pdf_data"] = serializer.data.get("pdf_data")
        return Response(serialized_data, status=HTTP_200_OK)


class GetWithPDFs(APIView):
    """Get annual reports with PDFs"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports_with_pdfs = AnnualReport.objects.exclude(pdf__isnull=True)
        serializer = TinyAnnualReportSerializer(
            reports_with_pdfs,
            context={"request": request},
            many=True,
        )
        return Response(serializer.data, status=HTTP_200_OK)


class GetLegacyPDFs(APIView):
    """Get legacy annual report PDFs"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        legacy_items = LegacyAnnualReportPDF.objects.all()
        serializer = TinyLegacyAnnualReportPDFSerializer(
            legacy_items,
            context={"request": request},
            many=True,
        )
        return Response(serializer.data, status=HTTP_200_OK)


class GetCompletedReports(APIView):
    """Get completed (published) annual reports"""

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
            return Response([], status=HTTP_200_OK)


class BeginAnnualReportDocGeneration(APIView):
    """Begin annual report document generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound

        # Placeholder for PDF generation logic
        # This will be implemented when PDF service is fully integrated
        return Response({"status": "generation_started"}, status=HTTP_200_OK)


class LatestYearsProgressReports(APIView):
    """Get latest year's approved progress reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings.LOGGER.info("Getting Approved Progress Reports for current year")

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # Get progress report documents for approved projects
            active_docs = ProgressReport.objects.filter(
                Q(report=latest_report)
                & Q(document__status="approved")
                & Q(
                    project__business_area__division__name="Biodiversity and Conservation Science"
                )
            ).exclude(Q(project__business_area__division__name__isnull=True))

            serializer = ProgressReportSerializer(
                active_docs, many=True, context={"request": request}
            )
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class LatestYearsStudentReports(APIView):
    """Get latest year's approved student reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings.LOGGER.info("Getting Approved Student Reports for current year")

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # Get student report documents for approved projects
            active_docs = StudentReport.objects.filter(
                Q(report=latest_report)
                & Q(document__status="approved")
                & Q(
                    project__business_area__division__name="Biodiversity and Conservation Science"
                )
            ).exclude(Q(project__business_area__division__name__isnull=True))

            serializer = StudentReportSerializer(
                active_docs, many=True, context={"request": request}
            )
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class LatestYearsInactiveReports(APIView):
    """Get latest year's inactive (non-approved) reports"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # Get non-approved student reports
            inactive_srs = (
                StudentReport.objects.filter(
                    Q(report=latest_report)
                    & Q(
                        project__business_area__division__name="Biodiversity and Conservation Science"
                    )
                )
                .exclude(document__status__in=["approved"])
                .exclude(Q(project__business_area__division__name__isnull=True))
                .all()
            )

            # Get non-approved progress reports
            inactive_prs = (
                ProgressReport.objects.filter(
                    Q(report=latest_report)
                    & Q(
                        project__business_area__division__name="Biodiversity and Conservation Science"
                    )
                )
                .exclude(document__status__in=["approved"])
                .exclude(Q(project__business_area__division__name__isnull=True))
                .all()
            )

            sr_serializer = StudentReportSerializer(
                inactive_srs, many=True, context={"request": request}
            )
            pr_serializer = ProgressReportSerializer(
                inactive_prs, many=True, context={"request": request}
            )

            return Response(
                {
                    "student_reports": sr_serializer.data,
                    "progress_reports": pr_serializer.data,
                },
                status=HTTP_200_OK,
            )
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class FullLatestReport(APIView):
    """Get full details of latest annual report"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            serializer = AnnualReportSerializer(
                latest_report,
                context={"request": request},
            )
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(status=HTTP_404_NOT_FOUND)
