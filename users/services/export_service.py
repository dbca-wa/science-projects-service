"""
Export service for data export operations
"""
import csv
from django.http import HttpResponse
from django.conf import settings

from users.models import PublicStaffProfile


class ExportService:
    """Business logic for data export operations"""

    @staticmethod
    def generate_staff_csv():
        """
        Generate CSV export of all staff profiles
        
        Returns:
            HttpResponse with CSV data
        """
        settings.LOGGER.info("Generating staff CSV export")
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="staff_profiles.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID',
            'First Name',
            'Last Name',
            'Email',
            'Business Area',
            'Position',
            'Is Active',
            'Public',
        ])
        
        profiles = PublicStaffProfile.objects.select_related(
            'user',
            'user__work',
            'user__work__business_area',
        ).filter(is_active=True)
        
        for profile in profiles:
            writer.writerow([
                profile.id,
                profile.user.first_name,
                profile.user.last_name,
                profile.user.email,
                profile.user.work.business_area.name if profile.user.work else '',
                profile.user.work.title if profile.user.work else '',
                profile.is_active,
                profile.public,
            ])
        
        return response
