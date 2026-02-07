"""
Export service - CSV export functionality
"""

import csv

from bs4 import BeautifulSoup
from django.conf import settings
from django.http import HttpResponse

from documents.models import AnnualReport
from users.models import User

from ..models import Project


class ExportService:
    """Business logic for project export operations"""

    @staticmethod
    def strip_html_tags(html_string):
        """Strip HTML tags and return plain text"""
        if not html_string:
            return ""
        soup = BeautifulSoup(html_string, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    @staticmethod
    def export_all_projects_csv(user):
        """
        Export all projects to CSV

        Args:
            user: User requesting the export

        Returns:
            HttpResponse with CSV content
        """
        settings.LOGGER.info(f"{user} is generating a csv of all projects...")

        try:
            # Retrieve projects with optimization
            projects = (
                Project.objects.select_related("business_area")
                .prefetch_related("members__user")
                .all()
            )

            # Create CSV response
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="projects-full.csv"'

            writer = csv.writer(response)

            # CSV headers
            headers = [
                "ID",
                "Project Code",
                "Status",
                "Type",
                "Year",
                "Title",
                "Business Area",
                "Business Area Leader",
                "Team Members",
                "Cost Center ID",
                "Start Date",
                "End Date",
            ]
            writer.writerow(headers)

            # Write project rows
            for project in projects:
                # Get business area leader
                ba_leader = ""
                if project.business_area and project.business_area.leader_id:
                    try:
                        leader_user = User.objects.filter(
                            pk=project.business_area.leader_id
                        ).first()
                        if leader_user:
                            ba_leader = str(leader_user)
                    except Exception as e:
                        settings.LOGGER.warning(
                            f"Failed to get business area leader for project {project.pk}: {e}"
                        )

                # Get team members
                team_members = []
                for project_member in project.members.all():
                    try:
                        if project_member.user:
                            team_members.append(
                                f"{project_member.user.first_name} {project_member.user.last_name}"
                            )
                    except Exception as e:
                        settings.LOGGER.warning(
                            f"Failed to get team member for project {project.pk}: {e}"
                        )
                        continue

                row = [
                    project.pk,
                    project.get_project_tag(),
                    project.status,
                    project.kind,
                    project.year,
                    ExportService.strip_html_tags(project.title),
                    project.business_area,
                    ba_leader,
                    ", ".join(team_members),
                    project.business_area.cost_center if project.business_area else "",
                    project.start_date,
                    project.end_date,
                ]
                writer.writerow(row)

            return response

        except Exception as e:
            settings.LOGGER.error(f"{e}")
            return HttpResponse(status=500, content="Error generating CSV")

    @staticmethod
    def export_annual_report_projects_csv(user):
        """
        Export annual report projects to CSV

        Args:
            user: User requesting the export

        Returns:
            HttpResponse with CSV content
        """
        settings.LOGGER.info(f"{user} is generating a csv of annual report projects...")

        try:
            # Get latest annual report
            latest_annual_report = AnnualReport.objects.order_by("-year").first()

            if not latest_annual_report:
                return HttpResponse(status=404, content="No annual reports found")

            # Get projects in progress reports
            progress_report_projects = Project.objects.filter(
                progress_reports__report=latest_annual_report
            ).distinct()

            # Get projects in student reports
            student_report_projects = Project.objects.filter(
                student_reports__report=latest_annual_report
            ).distinct()

            # Combine and remove duplicates
            annual_report_projects = (
                progress_report_projects | student_report_projects
            ).distinct()

            # Create CSV response
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="projects-annual-report-{latest_annual_report.year}.csv"'
            )

            writer = csv.writer(response)

            # CSV headers
            headers = [
                "ID",
                "Project Code",
                "Status",
                "Type",
                "Year",
                "Title",
                "Business Area",
                "Business Area Leader",
                "Team Members",
                "Cost Center ID",
                "Start Date",
                "End Date",
                "Report Type",
            ]
            writer.writerow(headers)

            # Write project rows
            for project in annual_report_projects:
                # Determine report type
                has_progress_report = project.progress_reports.filter(
                    report=latest_annual_report
                ).exists()
                has_student_report = project.student_reports.filter(
                    report=latest_annual_report
                ).exists()

                if has_progress_report and has_student_report:
                    report_type = "Progress & Student"
                elif has_progress_report:
                    report_type = "Progress"
                elif has_student_report:
                    report_type = "Student"
                else:
                    report_type = "Unknown"

                # Get business area leader
                ba_leader = ""
                if project.business_area and project.business_area.leader_id:
                    try:
                        leader_user = User.objects.filter(
                            pk=project.business_area.leader_id
                        ).first()
                        if leader_user:
                            ba_leader = str(leader_user)
                    except Exception as e:
                        settings.LOGGER.warning(
                            f"Failed to get business area leader for project {project.pk}: {e}"
                        )

                # Get team members
                team_members = []
                for project_member in project.members.all():
                    try:
                        if project_member.user:
                            team_members.append(
                                f"{project_member.user.first_name} {project_member.user.last_name}"
                            )
                    except Exception as e:
                        settings.LOGGER.warning(
                            f"Failed to get team member for project {project.pk}: {e}"
                        )
                        continue

                row = [
                    project.pk,
                    project.get_project_tag(),
                    project.status,
                    project.kind,
                    project.year,
                    ExportService.strip_html_tags(project.title),
                    project.business_area,
                    ba_leader,
                    ", ".join(team_members),
                    project.business_area.cost_center if project.business_area else "",
                    project.start_date,
                    project.end_date,
                    report_type,
                ]
                writer.writerow(row)

            return response

        except Exception as e:
            settings.LOGGER.error(f"{e}")
            return HttpResponse(status=500, content="Error generating CSV")
