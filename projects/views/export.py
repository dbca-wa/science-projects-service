"""
Project export views (CSV downloads)
"""
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from ..services.export_service import ExportService


class DownloadAllProjectsAsCSV(APIView):
    """Download all projects as CSV"""
    
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate and download CSV of all projects"""
        csv_content = ExportService.export_all_projects_csv(request.user)
        
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_projects.csv"'
        return response


class DownloadARProjectsAsCSV(APIView):
    """Download annual report projects as CSV"""
    
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Generate and download CSV of annual report projects"""
        csv_content = ExportService.export_annual_report_projects_csv(request.user)
        
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="annual_report_projects.csv"'
        return response
