"""
PDF generation views
"""

from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED
from rest_framework.views import APIView

from ..models import AnnualReport
from ..services.document_service import DocumentService
from ..services.pdf_service import PDFService


class DownloadProjectDocument(APIView):
    """Download project document PDF"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Download project document PDF"""
        document = DocumentService.get_document(pk)

        # Check if PDF exists
        if hasattr(document, "pdf") and document.pdf:
            return FileResponse(
                document.pdf.file,
                as_attachment=True,
                filename=f"{document.kind}_{document.pk}.pdf",
            )

        # Generate PDF if not exists
        pdf_file = PDFService.generate_document_pdf(document)

        return FileResponse(pdf_file, as_attachment=True, filename=pdf_file.name)


class BeginProjectDocGeneration(APIView):
    """Start project document PDF generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Start PDF generation for project document"""
        document = DocumentService.get_document(pk)

        # Mark as in progress
        PDFService.mark_pdf_generation_started(document)

        # TODO: Trigger async PDF generation task
        # For now, generate synchronously
        try:
            PDFService.generate_document_pdf(document)
            # Save PDF to document
            # document.pdf.save(pdf_file.name, pdf_file)
            PDFService.mark_pdf_generation_complete(document)
        except Exception:
            PDFService.mark_pdf_generation_complete(document)
            raise

        return Response(
            {"message": "PDF generation started", "document_id": document.pk},
            status=HTTP_202_ACCEPTED,
        )


class CancelProjectDocGeneration(APIView):
    """Cancel project document PDF generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Cancel PDF generation"""
        document = DocumentService.get_document(pk)
        PDFService.cancel_pdf_generation(document)

        return Response({"message": "PDF generation cancelled"}, status=HTTP_200_OK)


class DownloadAnnualReport(APIView):
    """Download annual report PDF"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Download annual report PDF"""
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound(f"Annual report {pk} not found")

        # Check if PDF exists
        if hasattr(report, "pdf") and report.pdf:
            return FileResponse(
                report.pdf.file,
                as_attachment=True,
                filename=f"annual_report_{report.year}.pdf",
            )

        # Generate PDF if not exists
        pdf_file = PDFService.generate_annual_report_pdf(report)

        return FileResponse(pdf_file, as_attachment=True, filename=pdf_file.name)


class BeginAnnualReportDocGeneration(APIView):
    """Start annual report PDF generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Start PDF generation for annual report"""
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound(f"Annual report {pk} not found")

        # Mark as in progress
        PDFService.mark_pdf_generation_started(report)

        # TODO: Trigger async PDF generation task
        # For now, generate synchronously
        try:
            PDFService.generate_annual_report_pdf(report)
            # Save PDF to report
            # report.pdf.save(pdf_file.name, pdf_file)
            PDFService.mark_pdf_generation_complete(report)
        except Exception:
            PDFService.mark_pdf_generation_complete(report)
            raise

        return Response(
            {"message": "PDF generation started", "report_id": report.pk},
            status=HTTP_202_ACCEPTED,
        )


class CancelReportDocGeneration(APIView):
    """Cancel annual report PDF generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Cancel PDF generation"""
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound(f"Annual report {pk} not found")

        PDFService.cancel_pdf_generation(report)

        return Response({"message": "PDF generation cancelled"}, status=HTTP_200_OK)
