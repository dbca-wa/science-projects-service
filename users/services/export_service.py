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
            'Is Hidden',
        ])
        
        profiles = PublicStaffProfile.objects.select_related(
            'user',
            'user__work',
            'user__work__business_area',
        ).filter(is_hidden=False)
        
        for profile in profiles:
            user_work = getattr(profile.user, 'work', None)
            writer.writerow([
                profile.id,
                profile.user.first_name,
                profile.user.last_name,
                profile.user.email,
                user_work.business_area.name if user_work and user_work.business_area else '',
                user_work.role if user_work else '',
                profile.is_hidden,
            ])
        
        return response
