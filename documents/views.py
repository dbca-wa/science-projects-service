import datetime
import json
import logging
import os
import re
import subprocess
import time
from bs4 import BeautifulSoup
from django.shortcuts import render
from agencies.models import BusinessArea
from communications.models import Comment
from communications.serializers import (
    TinyCommentCreateSerializer,
    TinyCommentSerializer,
)
from django.core.exceptions import ObjectDoesNotExist

# from config.tasks import generate_pdf
from projects.models import Project, ProjectMember
from django.template.loader import render_to_string
import html2text
import base64
from operator import attrgetter

from django.core.serializers.json import DjangoJSONEncoder

from email.mime.image import MIMEImage
from config.helpers import get_encoded_image

from medias.models import (
    AECEndorsementPDF,
    AnnualReportMedia,
    AnnualReportPDF,
    ProjectDocumentPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
)
from medias.serializers import (
    AECPDFCreateSerializer,
    AnnualReportPDFCreateSerializer,
    AnnualReportPDFSerializer,
    ProjectDocumentPDFSerializer,
    TinyAnnualReportPDFSerializer,
    TinyMethodologyImageSerializer,
    TinyProjectPhotoSerializer,
)
from projects.serializers import ARExternalProjectSerializer, ProjectSerializer
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
from django.db.models import Q, F, Prefetch

from .serializers import (
    AnnualReportSerializer,
    ConceptPlanCreateSerializer,
    ConceptPlanSerializer,
    EndorsementCreationSerializer,
    EndorsementSerializer,
    MiniAnnualReportSerializer,
    MiniEndorsementSerializer,
    ProgressReportAnnualReportSerializer,
    ProgressReportCreateSerializer,
    ProgressReportSerializer,
    ProjectClosureCreationSerializer,
    ProjectClosureSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
    ProjectPlanCreateSerializer,
    ProjectPlanSerializer,
    PublicationSerializer,
    StudentReportAnnualReportSerializer,
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
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from django.db.models import Max

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail, send_mass_mail

from django.template.loader import get_template

from django.template.loader import get_template
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


# PDF GENERATION ===================================================


class BeginReportDocGeneration(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound
        return obj

    def get_ar_media(self, pk, kind):
        try:
            obj = AnnualReportMedia.objects.get(report=pk, kind=kind)
        except AnnualReportMedia.DoesNotExist:
            print(f"AR MEDIA OF TYPE {kind} DOES NOT EXIST FOR AR {pk}")
            return None
        return obj

    def get_approved_external_projects_for_ar(self, report):
        settings.LOGGER.info(
            msg=f"Getting Approved External Projects for current year..."
        )
        if report:
            # print(report)
            # Get progress report documents which belong to it and belong to active and approved projects
            active_external_projects = Project.objects.filter(
                kind="external", status="active"
            ).exclude(
                Q(business_area__division__name__isnull=True)
                | ~Q(
                    business_area__division__name="Biodiversity and Conservation Science"
                )
            )

            # REPLACE WITH AR EXT PROJECT SERIALIAZER
            proj_ser = ARExternalProjectSerializer(
                active_external_projects,
                many=True,
            )

            return proj_ser.data
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )

    def get_approved_reports_for_ar(self, report):
        settings.LOGGER.info(
            msg=f"Getting Approved Student & Progress Reports for current year"
        )
        if report:
            # print(report)
            # Get progress report documents which belong to it and belong to active and approved projects
            active_sr_docs = StudentReport.objects.filter(
                report=report, project__status="active"
            ).exclude(
                Q(project__business_area__division__name__isnull=True)
                | ~Q(
                    project__business_area__division__name="Biodiversity and Conservation Science"
                )
            )

            active_pr_docs = ProgressReport.objects.filter(
                report=report, project__status="active"
            ).exclude(
                Q(project__business_area__division__name__isnull=True)
                | ~Q(
                    project__business_area__division__name="Biodiversity and Conservation Science"
                )
            )

            def removeempty_p(html_content):
                html_content = re.sub(r"<p>(&nbsp;|\s)*</p>", "", html_content)
                html_content = re.sub(r"&nbsp;", " ", html_content)

                return html_content

            for report in active_pr_docs:
                report.context = removeempty_p(report.context)
                report.aims = removeempty_p(report.aims)
                report.progress = removeempty_p(report.progress)
                report.implications = removeempty_p(report.implications)
                report.future = removeempty_p(report.future)

            # print(active_sr_docs)

            for sreport in active_sr_docs:
                sreport.progress_report = removeempty_p(sreport.progress_report)

            sr_ser = StudentReportAnnualReportSerializer(
                active_sr_docs,
                many=True,
            )
            pr_ser = ProgressReportAnnualReportSerializer(
                active_pr_docs,
                many=True,
            )

            # print(active_pr_docs)
            data_object = {
                "student_reports": sr_ser.data,
                "progress_reports": pr_ser.data,
            }
            # print(data_object["student_reports"])
            # print(data_object)
            return data_object
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is generating a pdf for report with id {pk}"
        )

        def set_report_generation_status(report, is_generating: bool):
            report.pdf_generation_in_progress = is_generating
            report.save()

        # Fetch Data for the templates
        report = self.go(pk=pk)
        # Return if already generating for report
        if report.pdf_generation_in_progress == True:
            return Response(
                {"error": "PDF Generation already in progress"},
                HTTP_400_BAD_REQUEST,
            )
        set_report_generation_status(report=report, is_generating=True)
        start_time = time.time()

        # Director's Message
        directors_message_data = report.dm

        # Publications
        publications_data = report.publications

        # Service Delivery Structure, ch img and chart

        generic_chapter_image = (
            os.path.join(settings.BASE_DIR, "documents", "generic_chapter_image.jpg")
            if os.path.exists(
                os.path.join(
                    settings.BASE_DIR, "documents", "generic_chapter_image.jpg"
                )
            )
            else ""
        )
        chart_image_obj = self.get_ar_media(pk=report.pk, kind="sdchart")
        sds_chapter_image_obj = self.get_ar_media(pk=report.pk, kind="service_delivery")
        sds_data = {
            "intro": report.service_delivery_intro,
            "chart": chart_image_obj.file.url if chart_image_obj else "",
            "chapter_image": (
                sds_chapter_image_obj.file.url
                if sds_chapter_image_obj
                else generic_chapter_image
            ),
        }
        # print(sds_data)

        # Other Chapter Images & Covers
        settings.LOGGER.info(msg=f"Fetching Annual Report Media...")
        cover_chapter_image = self.get_ar_media(pk=report.pk, kind="cover")
        rear_cover_chapter_image = self.get_ar_media(pk=report.pk, kind="rear_cover")

        research_chapter_image = self.get_ar_media(pk=report.pk, kind="research")
        partnerships_chapter_image = self.get_ar_media(
            pk=report.pk, kind="partnerships"
        )
        collaborations_chapter_image = self.get_ar_media(
            pk=report.pk, kind="collaborations"
        )
        student_projects_chapter_image = self.get_ar_media(
            pk=report.pk, kind="student_projects"
        )
        publications_chapter_image = self.get_ar_media(
            pk=report.pk, kind="publications"
        )

        cover_chapter_image = self.get_ar_media(pk=report.pk, kind="cover")
        rear_cover_chapter_image = self.get_ar_media(pk=report.pk, kind="rear_cover")

        research_chapter_image = (
            research_chapter_image.file.url
            if research_chapter_image
            else generic_chapter_image
        )
        partnerships_chapter_image = (
            partnerships_chapter_image.file.url
            if partnerships_chapter_image
            else generic_chapter_image
        )
        collaborations_chapter_image = (
            collaborations_chapter_image.file.url
            if collaborations_chapter_image
            else generic_chapter_image
        )
        student_projects_chapter_image = (
            student_projects_chapter_image.file.url
            if student_projects_chapter_image
            else generic_chapter_image
        )
        publications_chapter_image = (
            publications_chapter_image.file.url
            if publications_chapter_image
            else generic_chapter_image
        )

        cover_chapter_image = (
            cover_chapter_image.file.url
            if cover_chapter_image
            else generic_chapter_image
        )
        rear_cover_chapter_image = (
            rear_cover_chapter_image.file.url
            if rear_cover_chapter_image
            else generic_chapter_image
        )

        participating_external_projects = self.get_approved_external_projects_for_ar(
            report=report
        )
        # ext = []
        # for proj in participating_external_projects:
        #     title = proj["title"]
        #     partners = proj["partners"]
        #     funding = proj["funding"]
        #     members = proj.team_members

        # Participating Reports (Dict in format of student_reports, progress_reports)
        try:
            participating_reports = self.get_approved_reports_for_ar(report=report)
        except Exception as e:
            print(e)
            set_report_generation_status(report, False)

        # print(participating_reports["student_reports"])
        # print(participating_reports["progress_reports"])

        # Business Areas with Participating Projects
        bas = []
        for pr in participating_reports["progress_reports"]:
            document = pr["document"]
            project = document["project"]
            ba = project["business_area"]
            bas.append(ba)
        # print(bas)
        # order alphabetically
        sorted_bas = sorted(bas, key=lambda x: x["name"])

        def get_user_full_name(pk):
            try:
                u = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return ""
            return f"{u.first_name} {u.last_name}"

        def get_distilled_title(html_string):
            # Parse the HTML using BeautifulSoup
            soup = BeautifulSoup(html_string, "html.parser")

            # Extract the text content
            inner_text = soup.get_text(separator=" ", strip=True)

            return inner_text

        # Create a dictionary to group progress reports by business area pk
        progress_reports_by_ba = {}

        # Group progress reports based on business area pk
        for item in participating_reports["progress_reports"]:
            ba_pk = item["document"]["project"]["business_area"]["pk"]

            if ba_pk not in progress_reports_by_ba:
                progress_reports_by_ba[ba_pk] = []

            progress_reports_by_ba[ba_pk].append(item)

        sorted_external_project_data = []
        sorted_ba_data = []
        existing_ba_names = set()  # To keep track of existing ba_names

        # For each business area
        for ba in sorted_bas:
            ba_name = ba["name"]
            # Check if an object with the same ba_name already exists
            if ba_name not in existing_ba_names:
                # Create an object
                ba_object = {
                    "ba_name": ba_name,
                    "ba_image": ba["image"] if ba["image"] else "",
                    "ba_leader": get_user_full_name(ba["leader"]),
                    "ba_introduction": ba["introduction"],
                    # Prepare progress reports that match the business area's pk
                    "progress_reports": sorted(
                        progress_reports_by_ba.get(ba["pk"], []),
                        key=lambda x: get_distilled_title(
                            x["document"]["project"]["title"]
                        ),
                    ),
                }
                # Append the new ba_object
                sorted_ba_data.append(ba_object)

                # Add the ba_name to the set of existing ba_names
                existing_ba_names.add(ba_name)
        # Prep sections for each ba with the relevant projects
        # print(sorted_ba_data)

        # for item in sorted_ba_data:
        #     print(
        #         f"\n {item['ba_name']}\n{item['progress_reports'][0]['document']['project']['title']}"
        #     )

        sorted_srs = sorted(
            [
                report
                for report in participating_reports["student_reports"]
                if report["document"]["project"]
            ],
            key=lambda x: get_distilled_title(x["document"]["project"]["title"]),
        )

        external_partnerships_table_data = []
        #  Partners, Project Title, External Funding, Departmental Involvement (team)
        # (Alphabetical)

        student_projects_table_data = []
        # DBCA Officer, Student - student (level), Academic, Project Title, Duration, Page
        # (Alphabetical)

        research_projects_table_data = []
        # Use pre-existing data
        # BA, DBCA Region, IBRA/IMCRA, NRM Region, Project Title, Page
        # (Alphabetical BA Section & Project Title per section)

        # Handle Generation
        rte_css_path = os.path.join(settings.BASE_DIR, "documents", "rte_styles.css")
        prince_css_path = os.path.join(
            settings.BASE_DIR, "documents", "prince_ar_document_styles.css"
        )

        # Used the received css file to populate the backend css file
        css_content = req.data["css_content"]
        # print(css_content)
        formatted_css = css_content.replace("\\r\\n", "\n").replace('\\"', '"').strip()
        formatted_css = formatted_css.strip('"')
        # print(formatted_css)

        if css_content:
            with open(rte_css_path, "w") as saved_css_file:
                saved_css_file.write(formatted_css)

        dbca_image_path = os.path.join(
            settings.BASE_DIR, "documents", "BCSTransparent.png"
        )
        dbca_cropped_image_path = os.path.join(
            settings.BASE_DIR, "documents", "BCSTransparentCropped.png"
        )
        no_image_path = os.path.join(
            settings.BASE_DIR, "documents", "image_not_available.png"
        )

        # HTML content for the PDF
        def get_formatted_datetime(now):
            # Format the date and time
            day_with_suffix = "{}".format(now.day) + (
                "th"
                if 10 <= now.day % 100 <= 20
                else {1: "st", 2: "nd", 3: "rd"}.get(now.day % 10, "th")
            )

            formatted_datetime = now.strftime(f"{day_with_suffix} %B, %Y @ %I:%M%p")

            return formatted_datetime

        # "current_date_time_string": get_formatted_datetime(datetime.datetime.now()),

        settings.LOGGER.warn(msg=f"Annual Report Data Rendering to Template...")
        html_content = get_template("annual_report.html").render(
            {
                # Styles & url
                # "rte_css_path": rte_css_path,
                "time_generated": get_formatted_datetime(datetime.datetime.now()),
                "prince_css_path": prince_css_path,
                "dbca_image_path": dbca_image_path,
                "dbca_cropped_image_path": dbca_cropped_image_path,
                "no_image_path": no_image_path,
                "server_url": (
                    "http://127.0.0.1:8000"
                    if settings.DEBUG == True
                    # else settings.SITE_URL
                    else settings.PRINCE_SERVER_URL
                ),
                "frontend_url": (
                    "http://127.0.0.1:3000"
                    if settings.DEBUG == True
                    else settings.SITE_URL
                ),
                "base_url": settings.BASE_DIR,
                # Chapter Images
                "cover_chapter_image": cover_chapter_image,
                "rear_cover_chapter_image": rear_cover_chapter_image,
                "research_chapter_image": research_chapter_image,
                "partnerships_chapter_image": partnerships_chapter_image,
                "collaborations_chapter_image": collaborations_chapter_image,
                "student_projects_chapter_image": student_projects_chapter_image,
                "publications_chapter_image": publications_chapter_image,
                "generic_chapter_image_path": generic_chapter_image,
                # Cover page
                "financial_year_string": f"FY {int(report.year-1)}-{int(report.year)}",
                # ED Message
                "directors_message_data": directors_message_data,
                # TABLE CONTENTS
                # SDS
                "sds_data": sds_data,
                # BA & Progress Reports
                "sorted_ba_data_and_pr_dict": sorted_ba_data,
                # External Partnerships Table (OMMITTED - CALCULATED IN PRINCE)
                "sorted_external_project_data": participating_external_projects,
                # Student Report Table (OMMITTED - CALCULATED IN PRINCE)
                # Student Reports
                "sorted_student_report_array": sorted_srs,
                # Publications and Reports
                "publications_data": publications_data,
                # Summary of Research Projects (OMMITTED - CALCULATED IN PRINCE)
                "population_time": f"{float(time.time() - start_time):.3f}",
            }
        )

        end_time = time.time()
        elapsed_time = end_time - start_time
        settings.LOGGER.info(msg=f"Rendered to template in {elapsed_time:.6f} seconds.")

        # Specify the file path where you want to save the HTML file on the server
        html_file_path = os.path.join(
            settings.BASE_DIR,
            "documents",
            f"_Annual_Report_{report.pk}.html",
        )

        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

        # pdf_file_path = os.path.join(
        #     settings.BASE_DIR,
        #     "documents",
        #     f'{document_type}_{doc_data["project_pk"]}.pdf',
        # )

        # Combine all stylesheet paths into a single string separated by commas
        all_css_paths = ",".join([rte_css_path, prince_css_path])

        p = subprocess.Popen(
            ["prince", "-", f"--style={all_css_paths}", f"--javascript"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        outs, errs = p.communicate(f"{html_content}".encode("utf-8"))

        if p.returncode:
            # Handle `errs`.
            print(p.returncode)
            set_report_generation_status(report, False)

        else:
            pdf = outs
            # with open(pdf_file_path, "wb") as pdf_file:
            #     pdf_file.write(outs)
            #     print(f"Saved pdf file to {pdf_file_path}")

            pdf_filename = f"_Annual_Report_{report.pk}.pdf"
            file_content = ContentFile(pdf, name=pdf_filename)

            set_report_generation_status(report=report, is_generating=False)
            end_time = time.time()
            elapsed_time = end_time - start_time
            megabytes_size = len(pdf) / (1024**2)
            formatted_size = "{:.2f}".format(megabytes_size)
            settings.LOGGER.info(msg=f"PDF is " + str(formatted_size) + " MB in size")
            settings.LOGGER.info(
                msg=f"Annual Report PDF generated in {elapsed_time:.6f} seconds."
            )

            try:
                # Update item if it exists
                doc_pdf = AnnualReportPDF.objects.get(
                    report=report,
                )
                if doc_pdf:
                    ser = AnnualReportPDFSerializer(
                        doc_pdf,
                        data={
                            "file": file_content,
                        },
                        partial=True,
                    )
                    if ser.is_valid():
                        # Delete the previous file
                        pdfs_file_path = doc_pdf.file.path
                        default_storage.delete(pdfs_file_path)
                        doc_pdf = ser.save()
                        return Response(
                            AnnualReportPDFSerializer(doc_pdf).data,
                            status=HTTP_202_ACCEPTED,
                        )

                    else:
                        print("\n\nERROR HERE 1\n\n")
                        print("error on try ser")
                        print(ser.errors)

            except AnnualReportPDF.DoesNotExist:
                # If the item doesn't exist, create a new one
                ser = AnnualReportPDFCreateSerializer(
                    data={
                        "file": file_content,
                        "report": report.pk,
                        "creator": req.user.pk,
                    }
                )
                if ser.is_valid():
                    doc_pdf = ser.save()
                    return Response(
                        AnnualReportPDFSerializer(doc_pdf).data,
                        status=HTTP_201_CREATED,
                    )
                else:
                    print("error on except ser")
                    print(ser.errors)

        set_report_generation_status(report=report, is_generating=False)
        return Response(
            {"error": True},
            status=HTTP_400_BAD_REQUEST,
        )

        # set_report_generation_status(report=report, is_generating=False)

        return Response(
            {"msg": "ok"},
            HTTP_202_ACCEPTED,
        )


class CancelReportDocGeneration(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_main_doc(self, pk):
        # Gets the primary document that the concept plan belongs to
        try:
            doc = AnnualReport.objects.filter(pk=pk).first()
        except AnnualReport.DoesNotExist:
            raise NotFound
        return doc

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is canceling PDF GEN for Annual Report {pk}"
        )
        doc = self.get_main_doc(pk=pk)
        # doc.pdf_generation_in_progress = False
        # updated = doc.save()

        ser = AnnualReportSerializer(
            doc,
            data={"pdf_generation_in_progress": False},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            ser = AnnualReportSerializer(updated)
            settings.LOGGER.info(msg=f"Cancel Success")
            return Response(
                ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            print(ser.errors)
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class BeginProjectDocGeneration(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_main_doc(self, pk):
        # Gets the primary document that the concept plan belongs to
        try:
            doc = ProjectDocument.objects.filter(pk=pk).first()
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return doc

    def get_concept_plan(self, pk):
        # Gets the actual concept plan, with all the html data
        try:
            cp = ConceptPlan.objects.filter(document=pk).first()
        except ConceptPlan.DoesNotExist:
            raise NotFound
        return cp

    def get_project_plan(self, pk):
        # Gets the actual project plan, with all the html data
        try:
            pp = ProjectPlan.objects.filter(document=pk).first()
        except ProjectPlan.DoesNotExist:
            raise NotFound
        return pp

    def get_project_closure(self, pk):
        # Gets the actual project closure, with all the html data
        try:
            pc = ProjectClosure.objects.filter(document=pk).first()
        except ProjectClosure.DoesNotExist:
            raise NotFound
        return pc

    def get_progress_report(self, pk):
        # Gets the actual progress report, with all the html data
        try:
            pr = ProgressReport.objects.filter(document=pk).first()
        except ProgressReport.DoesNotExist:
            raise NotFound
        return pr

    def get_student_report(self, pk):
        # Gets the actual student report, with all the html data
        try:
            sr = StudentReport.objects.filter(document=pk).first()
        except StudentReport.DoesNotExist:
            raise NotFound
        return sr

    def post(self, req, pk):
        settings.LOGGER.info(msg=f"Generating Project Doc PDF")

        # print(req.data)

        doc = self.get_main_doc(pk=pk)
        document_type = doc.kind

        # General Helper Funcs
        def apply_title_styling_to_project_title(title):
            # Parse the HTML content
            soup = BeautifulSoup(title, "html.parser")

            # Create a new h1 tag
            h1_tag = soup.new_tag("h1")

            # Apply the specified styles to h1 tag
            h1_tag[
                "style"
            ] = """
                color: rgb(0, 102, 204);
                font-size: 24px; 
                font-weight: 400; 
                text-align: center; 
                padding: 0px; 
                margin-top: 2.5rem; 
                margin-bottom: 30px; 
                margin-left: 0px; 
                margin-right: 0px;
                cursor: pointer;
            """

            # Iterate through all b tags inside the p tag and set their style
            for strong_tag in soup.p.find_all("strong"):
                strong_tag[
                    "style"
                ] = """
                    color: rgb(0, 102, 204);
                """

            # Transfer content from p tag to h1 tag
            h1_tag.extend(soup.p.contents)

            # Replace the original p tag with the new h1 tag
            soup.p.replace_with(h1_tag)

            # Return the modified HTML as a string
            # print(f"\n{str(soup)}")
            return str(soup)

        def get_project_team(project_pk):
            # Get the member objects
            members = ProjectMember.objects.filter(project=project_pk).all()

            # Separate leader and other members
            leader = None
            other_members = []

            for member in members:
                if member.is_leader:
                    leader = member
                else:
                    other_members.append(member)

            # Sort other members based on their position value
            sorted_members = sorted(other_members, key=attrgetter("position"))

            # Create team_name_array with leader at the beginning and then other members
            team_name_array = []
            if leader:
                team_name_array.append(
                    f"{leader.user.first_name} {leader.user.last_name}"
                )

            for member in sorted_members:
                team_name_array.append(
                    f"{member.user.first_name} {member.user.last_name}"
                )

            return team_name_array

        def get_project_image(project_pk):
            try:
                image = ProjectPhoto.objects.get(project=project_pk)
            except ProjectPhoto.DoesNotExist:
                return None
            return image

        def get_methodology_image(project_pk):
            try:
                image = ProjectPlanMethodologyPhoto.objects.get(
                    project_plan__project=project_pk
                )
            except ProjectPlanMethodologyPhoto.DoesNotExist:
                return None
            return image

        def extract_html_table_data(html_data):
            # Extract relevant information from HTML table data and convert it to a list of lists using BeautifulSoup
            soup = BeautifulSoup(html_data, "html.parser")

            table_data = []
            for row in soup.find_all("tr"):
                row_data = [cell.text.strip() for cell in row.find_all(["th", "td"])]
                table_data.append(row_data)

            return table_data

        def iterate_rows_in_json_table(data_as_list):

            table_innards = []

            for row_index, row in enumerate(data_as_list):
                row_contents = "".join(
                    [
                        f"<{'th' if (row_index == 0 or col_index == 0) else 'td'} "
                        + f"class='table-cell-light{' table-cell-header-light' if row_index == 0 or col_index == 0 else ''}'>"
                        + f"{col}"
                        + f"</{'th' if (row_index == 0 or col_index == 0) else 'td'}>"
                        for col_index, col in enumerate(row)
                    ]
                )
                row_data = f"<tr>{row_contents}</tr>"
                table_innards.append(row_data)

            return_table = f'<table class="table-light">\
                <colgroup>\
                    {" ".join("<col>" for _ in range(len(data_as_list[0])))}\
                </colgroup>\
                <tbody>{"".join(table_innards)}</tbody>\
            </table>'
            return return_table

        def generate_html_table_from_json_data(table_data):
            if (
                isinstance(table_data, str)
                and table_data.startswith("[[")
                and table_data.endswith("]]")
            ):
                # Convert the string to a list using eval (Note: use eval cautiously)
                table_data = eval(table_data)
            elif (
                isinstance(table_data, str)
                and table_data.startswith("<table")
                and table_data.endswith("</table>")
            ):
                # If HTML data received, extract relevant information
                table_data = extract_html_table_data(table_data)
            elif isinstance(table_data, str):
                # If a string contains a table but doesn't both start and end with <table> tags, try to extract relevant information
                extracted_table_data = extract_html_table_data(table_data)
                if extracted_table_data:
                    table_data = extracted_table_data
            elif not all(isinstance(row, list) for row in table_data):
                # If neither JSON-like nor HTML-like data is received, raise an error
                raise ValueError(
                    f"Input must be a list of lists or a valid string representation of a list of lists or HTML table.\nProvided Input: {table_data}"
                )

            html = iterate_rows_in_json_table(eval(f"{table_data}"))

            # print(f"\nTABLE RAW DATA: {table_data}\n\nTABLE REPLACED DATA: {replaced_data}")

            return html

        def replace_table_in_html_string(html_data):

            # Avoid syntax errors within LInux due to nested f string
            def gen_html_table_from_list_structure(table_data):
                table_rows = "".join(
                    [
                        "<tr>{}</tr>".format(
                            "".join(
                                [
                                    "<{} {}>{}</{}>".format(
                                        (
                                            "th"
                                            if (row_index == 0 or col_index == 0)
                                            else "td"
                                        ),
                                        f"class='table-cell-light{' table-cell-header-light' if row_index == 0 or col_index == 0 else ''}'",
                                        col,
                                        (
                                            "th"
                                            if (row_index == 0 or col_index == 0)
                                            else "td"
                                        ),
                                    )
                                    for col_index, col in enumerate(row)
                                ]
                            )
                        )
                        for row_index, row in enumerate(table_data)
                    ]
                )
                # def gen_html_table_from_list_structure(table_data):
                #     table_rows = "".join(
                #         [

                #             f"<tr>{''.join(
                #                 [
                #                     f"<{'th' if (row_index == 0 or col_index == 0) else 'td'} "
                #                     + f"class='table-cell-light{' table-cell-header-light' if row_index == 0 or col_index == 0 else ''}'"
                #                     # + ">"
                #                     # + f" style='border: 1px solid black;'>" THE BORDER IS ALREADY IN STYLE (SEE HTML FILE), JUST NOT INTERPRETED BY PRINCE
                #                     + f">{col}"
                #                     + f"</{'th' if (row_index == 0 or col_index == 0) else 'td'}>"

                #                     for col_index, col in enumerate(row)
                #                 ]
                #             )}</tr>"

                #             for row_index, row in enumerate(table_data)
                #         ]
                #     )

                # Complete the HTML table
                replaced_data = f'<table class="table-light">\
                    <colgroup>\
                        {" ".join("<col>" for _ in range(len(table_data[0])))}\
                    </colgroup>\
                    <tbody>{table_rows}</tbody>\
                </table>'

                # print(f"\nTABLE RAW DATA: {table_data}\n\nTABLE REPLACED DATA: {replaced_data}")

                return replaced_data

            # print(f"DATA TO SOUP ({type(html_data)})", html_data,)
            if html_data is None:
                return "<p></p>"
            if (
                isinstance(html_data, str)
                and html_data.startswith("[[")
                and html_data.endswith("]]")
            ):
                # Convert the string to a list using eval and pass to the function
                html_data = iterate_rows_in_json_table(eval(html_data))
                # print("NEW HTML DATA: ", html_data)
                return html_data
            elif isinstance(html_data, str):
                soup = BeautifulSoup(html_data, "html.parser")

                for table_tag in soup.find_all("table"):
                    table_data = extract_html_table_data(str(table_tag))
                    if table_data:
                        new_table = gen_html_table_from_list_structure(table_data)
                        table_tag.replace_with(BeautifulSoup(new_table, "html.parser"))

                # print("SOUP:", soup)
                return str(soup)

        def replace_dark_with_light_style(html_string):
            if html_string != None:
                # Replace 'dark' with 'light' in class attributes
                modified_html = re.sub(
                    r'class\s*=\s*["\']([^"\']*dark[^"\']*)["\']',
                    lambda match: f'class="{match.group(1).replace("dark", "light")}"',
                    html_string,
                    flags=re.IGNORECASE,
                )

                # Add margin-left: 36px; to all <li> elements
                final_html = re.sub(
                    r"<li", r'<li style="margin-left: 36px;"', modified_html
                )

                return final_html
            else:
                return html_string

        def apply_styling(html_string):
            html_string = replace_dark_with_light_style(html_string=html_string)
            html_string = replace_table_in_html_string(html_string)
            return html_string

        def get_formatted_datetime(now):
            # Format the date and time
            day_with_suffix = "{}".format(now.day) + (
                "th"
                if 10 <= now.day % 100 <= 20
                else {1: "st", 2: "nd", 3: "rd"}.get(now.day % 10, "th")
            )

            formatted_datetime = now.strftime(f"{day_with_suffix} %B, %Y @ %I:%M%p")

            return formatted_datetime

        # Doc Data Get Funcs
        def return_proj_type_tag(document):
            kind = document.project.kind
            kind_dict = {
                "science": ["science", "SP"],
                "student": ["student", "STP"],
                "external": ["external", "EXT"],
                "core_function": ["core_function", "CF"],
            }

            return kind_dict[kind]

        def return_document_type_url(document, data_document=None):
            kind = document.kind
            if data_document:
                doc_year = data_document.year
                kind_dict = {
                    "concept": [
                        "concept",
                        "Science Concept Plan",
                        f"FY {int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "projectplan": [
                        "project",
                        "Science Project Plan",
                        f"FY {int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "progressreport": [
                        "progress",
                        "Progress Report",
                        f"FY {int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "studentreport": [
                        "student",
                        "Student Report",
                        f"FY {int(doc_year-1)}-{int(doc_year)}",
                    ],
                    "projectclosure": [
                        "closure",
                        "Project Closure",
                        f"FY {int(doc_year-1)}-{int(doc_year)}",
                    ],
                }
            else:
                kind_dict = {
                    "concept": ["concept", "Science Concept Plan"],
                    "projectplan": ["project", "Science Project Plan"],
                    "progressreport": ["progress", "Progress Report"],
                    "studentreport": ["student", "Student Report"],
                    "projectclosure": ["closure", "Project Closure"],
                }

            # If optional_arg is not provided, return 2 items
            # print(f"DOC KIND: {kind}\nDOC STRING: {kind_dict[kind]}")
            return kind_dict[kind]

        # Concept Plan
        def get_concept_plan_data():
            print("Gettin CP DATA")
            concept_plan_data = self.get_concept_plan(pk=pk)
            # print(concept_plan_data)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=concept_plan_data.document
            )
            doc_kind_url, doc_kind_str = return_document_type_url(
                document=concept_plan_data.document
            )

            document_tag = f"{project_kind_tag}-{concept_plan_data.project.year}-{concept_plan_data.project.number}"
            project_title = apply_title_styling_to_project_title(
                concept_plan_data.project.title
            )
            project_status = concept_plan_data.project.status
            business_area_name = concept_plan_data.project.business_area.name

            project_team = get_project_team(concept_plan_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(concept_plan_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                concept_plan_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                concept_plan_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                concept_plan_data.document.directorate_approval_granted
            )

            background = concept_plan_data.background
            aims = concept_plan_data.aims
            expected_outcomes = concept_plan_data.outcome
            collaborations = concept_plan_data.collaborations
            strategic_context = concept_plan_data.strategic_context
            staff_time_allocation = concept_plan_data.staff_time_allocation
            indicative_operating_budget = concept_plan_data.budget

            data_document_pk = concept_plan_data.pk
            main_document_pk = concept_plan_data.document.pk
            project_pk = concept_plan_data.project.pk

            return {
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "background": background,
                "aims": aims,
                "expected_outcomes": expected_outcomes,
                "collaborations": collaborations,
                "strategic_context": strategic_context,
                "staff_time_allocation": staff_time_allocation,
                "indicative_operating_budget": indicative_operating_budget,
            }

        # Project Plan
        def get_project_plan_data():
            project_plan_data = self.get_project_plan(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=project_plan_data.document
            )
            doc_kind_url, doc_kind_str = return_document_type_url(
                document=project_plan_data.document
            )

            document_tag = f"{project_kind_tag}-{project_plan_data.project.year}-{project_plan_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                project_plan_data.project.title
            )
            project_status = project_plan_data.project.status
            business_area_name = project_plan_data.project.business_area.name

            project_team = get_project_team(project_plan_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(project_plan_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            methodology_image_data = TinyMethodologyImageSerializer(
                get_methodology_image(project_plan_data.project.pk)
            ).data

            if "file" in methodology_image_data:
                methodology_image = methodology_image_data["file"]
            else:
                methodology_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                project_plan_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                project_plan_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                project_plan_data.document.directorate_approval_granted
            )

            background = project_plan_data.background
            aims = project_plan_data.aims
            expected_outcomes = project_plan_data.outcome

            knowledge_transfer = project_plan_data.knowledge_transfer
            project_tasks = project_plan_data.project_tasks
            listed_references = project_plan_data.listed_references
            methodology = project_plan_data.methodology
            consolidated_funds = project_plan_data.operating_budget
            external_funds = project_plan_data.operating_budget_external
            related_projects = project_plan_data.related_projects

            # strategic_context = project_plan_data.strategic_context
            # staff_time_allocation = replace_json_string_with_html_table(
            #     project_plan_data.staff_time_allocation
            # )
            # indicative_operating_budget = replace_json_string_with_html_table(
            #     project_plan_data.budget
            # )

            # Get the endorsement specific items
            endorsements = Endorsement.objects.filter(
                project_plan=project_plan_data.pk
            ).first()
            specimens = endorsements.no_specimens
            data_management = endorsements.data_management

            data_document_pk = project_plan_data.pk
            main_document_pk = project_plan_data.document.pk
            project_pk = project_plan_data.project.pk

            return {
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "methodology_image": methodology_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "background": background,
                "aims": aims,
                "expected_outcomes": expected_outcomes,
                "knowledge_transfer": knowledge_transfer,
                "project_tasks": project_tasks,
                "listed_references": listed_references,
                "methodology": methodology,
                "specimens": specimens,
                "data_management": data_management,
                "external_funds": external_funds,
                "consolidated_funds": consolidated_funds,
                "related_projects": related_projects,
            }

        # Progress Report
        def get_progress_report_data():
            progress_report_data = self.get_progress_report(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=progress_report_data.document
            )
            doc_kind_url, doc_kind_str, financial_year_string = (
                return_document_type_url(
                    document=progress_report_data.document,
                    data_document=progress_report_data,
                )
            )
            document_tag = f"{project_kind_tag}-{progress_report_data.project.year}-{progress_report_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                progress_report_data.project.title
            )
            project_status = progress_report_data.project.status
            business_area_name = progress_report_data.project.business_area.name

            project_team = get_project_team(progress_report_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(progress_report_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                progress_report_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                progress_report_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                progress_report_data.document.directorate_approval_granted
            )

            context = progress_report_data.context
            aims = progress_report_data.aims
            progress = progress_report_data.progress
            implications = progress_report_data.implications
            future = progress_report_data.future

            # strategic_context = project_plan_data.strategic_context
            # staff_time_allocation = replace_json_string_with_html_table(
            #     project_plan_data.staff_time_allocation
            # )
            # indicative_operating_budget = replace_json_string_with_html_table(
            #     project_plan_data.budget
            # )

            data_document_pk = progress_report_data.pk
            main_document_pk = progress_report_data.document.pk
            project_pk = progress_report_data.project.pk

            return {
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "financial_year_string": financial_year_string,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "context": context,
                "aims": aims,
                "progress": progress,
                "implications": implications,
                "future": future,
            }

        # Student Report
        def get_student_report_data():
            student_report_data = self.get_student_report(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=student_report_data.document
            )
            doc_kind_url, doc_kind_str, financial_year_string = (
                return_document_type_url(
                    document=student_report_data.document,
                    data_document=student_report_data,
                )
            )
            document_tag = f"{project_kind_tag}-{student_report_data.project.year}-{student_report_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                student_report_data.project.title
            )
            project_status = student_report_data.project.status
            business_area_name = student_report_data.project.business_area.name

            project_team = get_project_team(student_report_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(student_report_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                student_report_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                student_report_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                student_report_data.document.directorate_approval_granted
            )

            # strategic_context = project_plan_data.strategic_context
            # staff_time_allocation = replace_json_string_with_html_table(
            #     project_plan_data.staff_time_allocation
            # )
            # indicative_operating_budget = replace_json_string_with_html_table(
            #     project_plan_data.budget
            # )
            progress_report = student_report_data.progress_report

            data_document_pk = student_report_data.pk
            main_document_pk = student_report_data.document.pk
            project_pk = student_report_data.project.pk

            return {
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "financial_year_string": financial_year_string,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "progress_report": progress_report,
            }

        # Project Closure
        def get_project_closure_data():
            project_closure_data = self.get_project_closure(pk=pk)
            project_kind, project_kind_tag = return_proj_type_tag(
                document=project_closure_data.document
            )
            doc_kind_url, doc_kind_str = return_document_type_url(
                document=project_closure_data.document
            )

            document_tag = f"{project_kind_tag}-{project_closure_data.project.year}-{project_closure_data.project.number}"

            project_title = apply_title_styling_to_project_title(
                project_closure_data.project.title
            )
            project_status = project_closure_data.project.status
            business_area_name = project_closure_data.project.business_area.name

            project_team = get_project_team(project_closure_data.project.pk)

            project_image_data = TinyProjectPhotoSerializer(
                get_project_image(project_closure_data.project.pk)
            ).data

            if "file" in project_image_data:
                project_image = project_image_data["file"]
            else:
                project_image = ""

            now = datetime.datetime.now()

            project_lead_approval_granted = (
                project_closure_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                project_closure_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                project_closure_data.document.directorate_approval_granted
            )

            reason = project_closure_data.reason
            knowledge_transfer = project_closure_data.knowledge_transfer
            data_location = project_closure_data.data_location
            hardcopy_location = project_closure_data.hardcopy_location
            backup_location = project_closure_data.backup_location
            scientific_outputs = project_closure_data.scientific_outputs
            intended_outcome = project_closure_data.intended_outcome

            # strategic_context = project_plan_data.strategic_context
            # staff_time_allocation = replace_json_string_with_html_table(
            #     project_plan_data.staff_time_allocation
            # )
            # indicative_operating_budget = replace_json_string_with_html_table(
            #     project_plan_data.budget
            # )

            data_document_pk = project_closure_data.pk
            main_document_pk = project_closure_data.document.pk
            project_pk = project_closure_data.project.pk

            return {
                "project_kind": project_kind,
                "document_kind_url": doc_kind_url,
                "document_kind_string": doc_kind_str,
                "doc_kind_url": doc_kind_url,
                "document_data_pk": data_document_pk,
                "document_pk": main_document_pk,
                "project_pk": project_pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                # Specific
                "reason": reason,
                "knowledge_transfer": knowledge_transfer,
                "data_location": data_location,
                "hardcopy_location": hardcopy_location,
                "backup_location": backup_location,
                "scientific_outputs": scientific_outputs,
                "intended_outcome": intended_outcome,
            }

        # Doc Wide Variables
        rte_css_path = os.path.join(settings.BASE_DIR, "documents", "rte_styles.css")
        prince_css_path = os.path.join(
            settings.BASE_DIR, "documents", "prince_project_document_styles.css"
        )

        # Used the received css file to populate the backend css file
        css_content = req.data["css_content"]
        # print(css_content)
        formatted_css = css_content.replace("\\r\\n", "\n").replace('\\"', '"').strip()
        formatted_css = formatted_css.strip('"')
        # print(formatted_css)

        if css_content:
            with open(rte_css_path, "w") as saved_css_file:
                saved_css_file.write(formatted_css)

        dbca_image_path = os.path.join(
            settings.BASE_DIR, "documents", "BCSTransparent.png"
        )
        dbca_cropped_image_path = os.path.join(
            settings.BASE_DIR, "documents", "BCSTransparentCropped.png"
        )
        no_image_path = os.path.join(
            settings.BASE_DIR, "documents", "image_not_available.png"
        )

        # Get innerhtml of element
        def get_inner_html(html_content, html_tag):
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Find the element by its tag
            element = soup.find(html_tag)

            # Check if the element is found
            if element:
                # Get the inner HTML of the element
                inner_html = str(element.decode_contents())

                return inner_html
            else:
                return None

        # Begin
        doc.pdf_generation_in_progress = True
        doc.save()

        if document_type == "concept":
            doc_data = get_concept_plan_data()
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "background": {
                            "title": "Background",
                            "data": apply_styling(doc_data["background"]),
                        },
                        "aims": {
                            "title": "Aims",
                            "data": apply_styling(doc_data["aims"]),
                        },
                        "outcomes": {
                            "title": "Expected Outcomes",
                            "data": apply_styling(doc_data["expected_outcomes"]),
                        },
                        "context": {
                            "title": "Strategic Context",
                            "data": apply_styling(doc_data["strategic_context"]),
                        },
                        "collaborations": {
                            "title": "Expected Collaborations",
                            "data": apply_styling(doc_data["collaborations"]),
                        },
                        "staff_time_allocation": {
                            "title": "Staff Time Allocation",
                            "data": generate_html_table_from_json_data(
                                apply_styling(doc_data["staff_time_allocation"])
                            ),
                        },
                        "indicative_operating_budget": {
                            "title": "Budget",
                            "data": generate_html_table_from_json_data(
                                apply_styling(doc_data["indicative_operating_budget"])
                            ),
                        },
                    },
                }
            )

        elif document_type == "projectplan":
            doc_data = get_project_plan_data()
            # print(doc_data)
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "methodology_image": doc_data["methodology_image"],
                    "html_data_items": {
                        "background": {
                            "title": "Background",
                            "data": apply_styling(doc_data["background"]),
                        },
                        "aims": {
                            "title": "Aims",
                            "data": apply_styling(doc_data["aims"]),
                        },
                        "outcomes": {
                            "title": "Expected Outcomes",
                            "data": apply_styling(doc_data["expected_outcomes"]),
                        },
                        "knowledge_transfer": {
                            "title": "Knowledge Transfer",
                            "data": apply_styling(doc_data["knowledge_transfer"]),
                        },
                        "project_tasks": {
                            "title": "Tasks and Milestones",
                            "data": apply_styling(doc_data["project_tasks"]),
                        },
                        "listed_references": {
                            "title": "References",
                            "data": apply_styling(doc_data["listed_references"]),
                        },
                        "methodology": {
                            "title": "Methodology",
                            "data": apply_styling(doc_data["methodology"]),
                        },
                        "specimens": {
                            "title": "Number of Voucher Specimens",
                            "data": apply_styling(doc_data["specimens"]),
                        },
                        "data_management": {
                            "title": "Data Management",
                            "data": apply_styling(doc_data["data_management"]),
                        },
                        "related_projects": {
                            "title": "Related Science Projects",
                            "data": apply_styling(doc_data["related_projects"]),
                        },
                        "consolidated_funds": {
                            "title": "Consolidated Funds",
                            "data":
                            # generate_html_table_from_json_data(
                            apply_styling(doc_data["consolidated_funds"]),
                            # )
                        },
                        "external_funds": {
                            "title": "External Funds",
                            "data": generate_html_table_from_json_data(
                                # apply_styling(
                                doc_data["external_funds"]
                                # )
                            ),
                        },
                    },
                }
            )

        elif document_type == "progressreport":
            doc_data = get_progress_report_data()
            # print(doc_data)
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    "financial_year_string": doc_data["financial_year_string"],
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "context": {
                            "title": "Context",
                            "data": apply_styling(doc_data["context"]),
                        },
                        "aims": {
                            "title": "Aims",
                            "data": apply_styling(doc_data["aims"]),
                        },
                        "progress": {
                            "title": "Progress",
                            "data": apply_styling(doc_data["progress"]),
                        },
                        "implications": {
                            "title": "Management Implications",
                            "data": apply_styling(doc_data["implications"]),
                        },
                        "future": {
                            "title": "Future Directions",
                            "data": apply_styling(doc_data["future"]),
                        },
                    },
                }
            )
        elif document_type == "studentreport":
            doc_data = get_student_report_data()
            # print(doc_data)
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    "financial_year_string": doc_data["financial_year_string"],
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "progress_report": {
                            "title": "Progress Report",
                            "data": apply_styling(doc_data["progress_report"]),
                        },
                    },
                }
            )
        elif document_type == "projectclosure":
            doc_data = get_project_closure_data()
            # print(doc_data)
            # HTML content for the PDF
            html_content = get_template("project_document.html").render(
                {
                    # Styles & url
                    "rte_css_path": rte_css_path,
                    "prince_css_path": prince_css_path,
                    "dbca_image_path": dbca_image_path,
                    "dbca_cropped_image_path": dbca_cropped_image_path,
                    "no_image_path": no_image_path,
                    "server_url": (
                        "http://127.0.0.1:8000"
                        if settings.DEBUG == True
                        # else settings.SITE_URL
                        else settings.PRINCE_SERVER_URL
                    ),
                    "frontend_url": (
                        "http://127.0.0.1:3000"
                        if settings.DEBUG == True
                        else settings.SITE_URL
                    ),
                    # Cover page
                    "base_url": settings.BASE_DIR,
                    "current_date_time_string": get_formatted_datetime(doc_data["now"]),
                    "project_image_path": doc_data["project_image"],
                    "project_title": get_inner_html(doc_data["project_title"], "h1"),
                    "project_tag": doc_data["document_tag"],
                    "business_area_name": doc_data["business_area_name"],
                    "project_status": doc_data["project_status"],
                    "team_as_string": ", ".join(map(str, doc_data["project_team"])),
                    "project_lead_approval": doc_data["project_lead_approval_granted"],
                    "business_area_lead_approval": doc_data[
                        "business_area_lead_approval_granted"
                    ],
                    "directorate_approval": doc_data["directorate_approval_granted"],
                    # Data
                    "document_kind_url": doc_data["document_kind_url"],
                    "document_kind_string": doc_data["document_kind_string"],
                    "project_kind": doc_data["project_kind"],
                    "project_id": doc_data["project_pk"],
                    "html_data_items": {
                        "reason": {
                            "title": "Reason",
                            "data": apply_styling(doc_data["reason"]),
                        },
                        "knowledge_transfer": {
                            "title": "Knowledge Transfer",
                            "data": apply_styling(doc_data["knowledge_transfer"]),
                        },
                        "data_location": {
                            "title": "Data Location",
                            "data": apply_styling(doc_data["data_location"]),
                        },
                        "hardcopy_location": {
                            "title": "Hardcopy Location",
                            "data": apply_styling(doc_data["hardcopy_location"]),
                        },
                        "backup_location": {
                            "title": "Backup Location",
                            "data": apply_styling(doc_data["backup_location"]),
                        },
                        "scientific_outputs": {
                            "title": "Scientific Outputs",
                            "data": apply_styling(doc_data["scientific_outputs"]),
                        },
                        "intended_outcome": {
                            "title": "Intended Outcome",
                            "data": apply_styling(doc_data["intended_outcome"]),
                        },
                    },
                }
            )
        else:
            return Response(
                {"err": "Invalid project type"},
                HTTP_400_BAD_REQUEST,
            )

        # Specify the file path where you want to save the HTML file on the server
        # html_file_path = os.path.join(
        #     settings.BASE_DIR,
        #     "documents",
        #     f'{document_type}_{doc_data["project_pk"]}.html',
        # )
        # with open(html_file_path, "w", encoding="utf-8") as html_file:
        #     html_file.write(html_content)

        # pdf_file_path = os.path.join(
        #     settings.BASE_DIR,
        #     "documents",
        #     f'{document_type}_{doc_data["project_pk"]}.pdf',
        # )

        # Combine all stylesheet paths into a single string separated by commas
        all_css_paths = ",".join([rte_css_path, prince_css_path])

        p = subprocess.Popen(
            ["prince", "-", f"--style={all_css_paths}", f"--javascript"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        outs, errs = p.communicate(f"{html_content}".encode("utf-8"))

        if p.returncode:
            # Handle `errs`.
            print(p.returncode)
            doc.pdf_generation_in_progress = True
            doc.save()

        else:
            pdf = outs
            print("PDF is " + str(len(pdf)) + " bytes in size")
            # with open(pdf_file_path, "wb") as pdf_file:
            #     pdf_file.write(outs)
            #     print(f"Saved pdf file to {pdf_file_path}")
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            if document_type == "progressreport" or document_type == "studentreport":
                pdf_filename = f'{doc_data["project_pk"]}_{document_kind_dict[document_type]} ({doc_data["financial_year_string"]}).pdf'
            else:
                pdf_filename = (
                    f'{doc_data["project_pk"]}_{document_kind_dict[document_type]}.pdf'
                )
            file_content = ContentFile(pdf, name=pdf_filename)

            doc.pdf_generation_in_progress = False
            doc.save()
            try:
                # Update item if it exists
                doc_pdf = ProjectDocumentPDF.objects.get(
                    document=doc, project=doc.project
                )

                ser = ProjectDocumentPDFSerializer(
                    doc_pdf,
                    data={
                        "file": file_content,
                    },
                    partial=True,
                )
                if ser.is_valid():
                    # Delete the previous file
                    pdfs_file_path = doc_pdf.file.path
                    default_storage.delete(pdfs_file_path)
                    doc_pdf = ser.save()
                    return Response(
                        ProjectDocumentPDFSerializer(doc_pdf).data,
                        status=HTTP_202_ACCEPTED,
                    )

                else:
                    print("Error saving PDF (try ser invalid)")
                    print(ser.errors)

            except ProjectDocumentPDF.DoesNotExist:
                # If the item doesn't exist, create a new one
                ser = ProjectDocumentPDFSerializer(
                    data={
                        "file": file_content,
                        "document": doc.pk,
                        "project": doc.project.pk,
                    }
                )
                if ser.is_valid():
                    doc_pdf = ser.save()
                    return Response(
                        ProjectDocumentPDFSerializer(doc_pdf).data,
                        status=HTTP_201_CREATED,
                    )
                else:
                    print("Error saving PDF (except ser invalid)")
                    print(ser.errors)

        return Response(
            {"error": True},
            status=HTTP_400_BAD_REQUEST,
        )


class CancelProjectDocGeneration(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_main_doc(self, pk):
        # Gets the primary document that the concept plan belongs to
        try:
            doc = ProjectDocument.objects.filter(pk=pk).first()
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return doc

    def post(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is canceling PDF GEN for document {pk}")
        doc = self.get_main_doc(pk=pk)
        # doc.pdf_generation_in_progress = False
        # updated = doc.save()

        ser = ProjectDocumentSerializer(
            doc,
            data={"pdf_generation_in_progress": False},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            ser = ProjectDocumentSerializer(updated)
            settings.LOGGER.info(msg=f"Cancel Success")
            return Response(
                ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            print(ser.errors)
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


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


class GetConceptPlanData(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            concept_plan_data = ConceptPlan.objects.get(pk=pk)  # document
        except ConceptPlan.DoesNotExist:
            raise NotFound
        return concept_plan_data

    def post(self, req, pk):

        def timing_wrapper(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f"{func.__name__} took {elapsed_time:.6f} seconds to run.")
                return result

            return wrapper

        # STEP 1: Get Concept Plan Data
        def get_concept_plan_data():
            concept_plan_data = self.go(pk=pk)
            print(concept_plan_data)

            document_tag = f"CF-{concept_plan_data.project.year}-{concept_plan_data.project.number}"
            project_title = concept_plan_data.project.title
            project_status = concept_plan_data.project.status
            business_area_name = concept_plan_data.project.business_area.name

            def get_project_team(project_pk):
                # Get the member objects
                members = ProjectMember.objects.filter(project=project_pk).all()

                # Separate leader and other members
                leader = None
                other_members = []

                for member in members:
                    if member.is_leader:
                        leader = member
                    else:
                        other_members.append(member)

                # Sort other members based on their position value
                sorted_members = sorted(other_members, key=attrgetter("position"))

                # Create team_name_array with leader at the beginning and then other members
                team_name_array = []
                if leader:
                    team_name_array.append(
                        f"{leader.user.first_name} {leader.user.last_name}"
                    )

                for member in sorted_members:
                    team_name_array.append(
                        f"{member.user.first_name} {member.user.last_name}"
                    )

                return team_name_array

            project_team = get_project_team(concept_plan_data.project.pk)

            def get_project_image(project_pk):
                try:
                    image = ProjectPhoto.objects.get(project=project_pk)
                except ProjectPhoto.DoesNotExist:
                    return None
                return image

            project_image = TinyProjectPhotoSerializer(
                get_project_image(concept_plan_data.project.pk)
            ).data

            now = datetime.datetime.now()

            # print({
            #     "document_tag": document_tag,
            #     "project_title": project_title,
            #     "project_status": project_status,
            #     "business_area_name": business_area_name,
            #     "project_team": tuple(project_team),
            #     "image": project_image,
            #     "now": now
            # })

            project_lead_approval_granted = (
                concept_plan_data.document.project_lead_approval_granted
            )
            business_area_lead_approval_granted = (
                concept_plan_data.document.business_area_lead_approval_granted
            )
            directorate_approval_granted = (
                concept_plan_data.document.directorate_approval_granted
            )

            # print({
            #     "project_lead_approval_granted": project_lead_approval_granted,
            #     "business_area_lead_approval_granted": business_area_lead_approval_granted,
            #     "directorate_approval_granted": directorate_approval_granted
            # })

            # pdf_generation_in_progress = models.BooleanField(default=False)

            def replace_json_string_with_html_table(input_string):
                try:
                    # Attempt to parse the input JSON string
                    data = json.loads(input_string)
                except json.JSONDecodeError:
                    # If parsing fails, return the original input string
                    return input_string

                # Begin constructing the HTML table with additional styling
                html_table = '<table class="table-light">\n  <colgroup>\n'
                html_table += '    <col style="background-color: rgb(242, 243, 245);">\n'  # Style for the leftmost column

                for _ in range(len(data[0])):
                    html_table += "    <col>\n"

                html_table += "  </colgroup>\n  <tbody>\n"

                for i, row in enumerate(data):
                    html_table += "    <tr>\n"
                    for j, cell in enumerate(row):
                        if i == 0:
                            # Apply background color to the first row
                            html_table += f'      <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\n'
                        elif j == 0:
                            # Apply background color to the leftmost column
                            html_table += f'      <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\n'
                        else:
                            html_table += f'      <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;">\n'

                        html_table += f'        <p class="editor-p-light" dir="ltr">\n'
                        html_table += f'          <span style="white-space: pre-wrap;">{cell}</span>\n'
                        html_table += f"        </p>\n"
                        html_table += "      </" + ("th" if i == 0 else "td") + ">\n"

                    html_table += "    </tr>\n"

                # Close the table
                html_table += "  </tbody>\n</table>"
                print(html_table)

                return html_table

            background = concept_plan_data.background
            aims = concept_plan_data.aims
            expected_outcomes = concept_plan_data.outcome
            collaborations = concept_plan_data.collaborations
            strategic_context = concept_plan_data.strategic_context
            staff_time_allocation = replace_json_string_with_html_table(
                concept_plan_data.staff_time_allocation
            )
            indicative_operating_budget = replace_json_string_with_html_table(
                concept_plan_data.budget
            )

            # print({
            #     "background": background,
            #     "aims": aims,
            #     "expected_outcomes": expected_outcomes,
            #     "collaborations": collaborations,
            #     "strategic_context": strategic_context,
            #     "staff_time_allocation": staff_time_allocation,
            #     "indicative_operating_budget": indicative_operating_budget,
            #     "project_pk": concept_plan_data.project.pk,
            # })

            return {
                "concept_plan_data_pk": concept_plan_data.pk,
                "document_pk": concept_plan_data.document.pk,
                "project_pk": concept_plan_data.project.pk,
                "document_tag": document_tag,
                "project_title": project_title,
                "project_status": project_status,
                "business_area_name": business_area_name,
                "project_team": tuple(project_team),
                "project_image": project_image,
                "now": now,
                "project_lead_approval_granted": project_lead_approval_granted,
                "business_area_lead_approval_granted": business_area_lead_approval_granted,
                "directorate_approval_granted": directorate_approval_granted,
                "background": background,
                "aims": aims,
                "expected_outcomes": expected_outcomes,
                "collaborations": collaborations,
                "strategic_context": strategic_context,
                "staff_time_allocation": staff_time_allocation,
                "indicative_operating_budget": indicative_operating_budget,
            }

        # data = get_concept_plan_data()

        timed_func = timing_wrapper(get_concept_plan_data)
        data = timed_func()

        return Response(
            data,
            HTTP_200_OK,
        )


# Latest Year's Reports


class BeginAnnualReportDocGeneration(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            report = AnnualReport.objects.get(pk=pk)
        except AnnualReport.DoesNotExist:
            raise NotFound
        return report

    def post(self, req, pk):
        report_object = self.go(pk=pk)


class LatestYearsProgressReports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(msg=f"Getting Approved Progress Reports for current year")

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # print(latest_report)
            # Get progress report documents which belong to it and belong to active and approved projects
            active_docs = ProgressReport.objects.filter(
                report=latest_report, project__status="active"
            ).exclude(
                Q(project__business_area__division__name__isnull=True)
                | ~Q(
                    project__business_area__division__name="Biodiversity and Conservation Science"
                )
            )
            # print(active_docs)
            ser = ProgressReportSerializer(
                active_docs, many=True, context={"request": req}
            )
            return Response(
                ser.data,
                HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


class LatestYearsStudentReports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(
            msg=f"Getting Approved Student Reports for current year..."
        )

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # print(latest_report)
            # Get progress report documents which belong to it and belong to active and approved projects
            active_docs = StudentReport.objects.filter(
                report=latest_report, project__status="active"
            ).exclude(
                Q(project__business_area__division__name__isnull=True)
                | ~Q(
                    project__business_area__division__name="Biodiversity and Conservation Science"
                )
            )
            # print(active_docs)
            ser = StudentReportSerializer(
                active_docs, many=True, context={"request": req}
            )
            return Response(
                ser.data,
                HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


class LatestYearsInactiveReports(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):

        # Get the latest year's report
        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            # print(latest_report)
            # Get progress report documents which belong to it and belong to active and approved projects
            inactive_srs = (
                StudentReport.objects.filter(report=latest_report)
                .exclude(project__status__in=["active"])
                .exclude(
                    Q(project__business_area__division__name__isnull=True)
                    | ~Q(
                        project__business_area__division__name="Biodiversity and Conservation Science"
                    )
                )
                .all()
            )
            inactive_prs = (
                ProgressReport.objects.filter(report=latest_report)
                .exclude(project__status__in=["active"])
                .exclude(
                    Q(project__business_area__division__name__isnull=True)
                    | ~Q(
                        project__business_area__division__name="Biodiversity and Conservation Science"
                    )
                )
                .all()
            )

            sr_ser = StudentReportSerializer(
                inactive_srs, many=True, context={"request": req}
            )
            pr_ser = ProgressReportSerializer(
                inactive_prs, many=True, context={"request": req}
            )

            res_dict = {
                "student_reports": sr_ser.data,
                "progress_reports": pr_ser.data,
            }

            return Response(
                res_dict,
                HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


class FullLatestReport(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):

        latest_report = AnnualReport.objects.order_by("-year").first()
        if latest_report:
            ser = AnnualReportSerializer(
                latest_report,
                context={"request": req},
            )
            return Response(
                ser.data,
                status=HTTP_200_OK,
            )
        else:
            return Response(
                HTTP_404_NOT_FOUND,
            )


# EMAILS ==========================================================


class ReviewDocumentEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Review Document) for users {req.data['recipients_list']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/review_document_email.html"

        # Get actioning user details (User causing email to be sent)
        actioning_user = User.objects.get(pk=req.user.pk)
        actioning_user_name = f"{actioning_user.first_name} {actioning_user.last_name}"
        actioning_user_email = f"{actioning_user.email}"

        # Get recipient list
        recipients_list_data = req.data["recipients_list"]  # list of user pks
        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get project information
        project_pk = req.data["project_pk"]
        project = Project.objects.filter(pk=project_pk).first()
        if project:
            html_project_title = project.title
            plain_project_name = html2text.html2text(
                html_project_title
            ).strip()  # nicely rendered html title

            # Get document kind information
            document_kind = req.data["document_kind"]
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            document_kind_as_title = document_kind_dict[document_kind]
            email_subject = f"SPMS: Review {document_kind_as_title}"

            for recipient in recipients_list:
                if recipient["pk"] == 101073:
                    to_email = [recipient["email"]]

                    template_props = {
                        "email_subject": email_subject,
                        "recipient_name": recipient["name"],
                        "actioning_user_email": actioning_user_email,
                        "actioning_user_name": actioning_user_name,
                        "project_id": project_pk,
                        "plain_project_name": plain_project_name,
                        "document_type": document_kind,
                        "document_type_title": document_kind_as_title,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    template_content = render_to_string(templ, template_props)
                    print(
                        {
                            "to_email": to_email,
                            "email_subject": email_subject,
                            "recipient_name": recipient["name"],
                            "actioning_user_email": actioning_user_email,
                            "actioning_user_name": actioning_user_name,
                            "project_id": project_pk,
                            "plain_project_name": plain_project_name,
                            "document_type": document_kind,
                            "document_type_title": document_kind_as_title,
                            "site_url": settings.SITE_URL,
                            "dbca_image_path": get_encoded_image(),
                        }
                    )

                    try:
                        send_mail(
                            email_subject,
                            template_content,  # plain text
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
            return Response(
                "Emails Sent!",
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                {"error": "No matching project"},
                status=HTTP_400_BAD_REQUEST,
            )


class NewCycleOpenEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (New Cycle Open) to Project Leads for active projects and all Business Area Leaders"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/new_cycle_open_email.html"

        # Get recipient list (ba leads)
        ba_leads = {ba.leader.pk for ba in BusinessArea.objects.all() if ba.leader}
        # Get recipient list (active project leads)
        also_updating = req.data["include_projects_with_status_updating"]
        if also_updating == True or also_updating == "True":
            active_project_leads = (
                ProjectMember.objects.filter(
                    project__status__in=["active", "updating"], is_leader=True
                )
                .values_list("user__pk", flat=True)
                .distinct()
            )
        else:
            active_project_leads = (
                ProjectMember.objects.filter(
                    project__status__in=["active"], is_leader=True
                )
                .values_list("user__pk", flat=True)
                .distinct()
            )

        # Get combined recipient list, without duplicates
        recipients_list_data = list(ba_leads.union(active_project_leads))

        print(recipients_list_data)

        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get FY information
        financial_year = req.data["financial_year"]
        financial_year_string = f"FY {int(financial_year-1)}-{int(financial_year)}"

        for recipient in recipients_list:
            if recipient["pk"] == 101073:
                email_subject = f"SPMS: {financial_year_string} Reporting Cycle Open"
                to_email = [recipient["email"]]

                template_props = {
                    "email_subject": email_subject,
                    "recipient_name": recipient["name"],
                    "site_url": settings.SITE_URL,
                    "dbca_image_path": get_encoded_image(),
                    "financial_year_string": financial_year_string,
                }

                template_content = render_to_string(templ, template_props)

                try:
                    send_mail(
                        email_subject,
                        template_content,  # plain text
                        from_email,
                        to_email,
                        fail_silently=False,  # Set this to False to see errors
                        html_message=template_content,
                    )
                except Exception as e:
                    settings.LOGGER.error(
                        msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                    )
                    return Response(
                        {"error": str(e)},
                        status=HTTP_400_BAD_REQUEST,
                    )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


class ProjectClosureEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Project Closure) to the project lead of project with id {req.data['project_pk']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/project_closed_email.html"

        # Get recipient list (ba leads)
        project_pk = req.data["project_pk"]
        project_leader = ProjectMember.objects.filter(
            project=project_pk, is_leader=True
        ).first()
        print("PROJECT LEADER: ", project_leader)
        if project_leader:
            recipients_list = []
            user = User.objects.get(pk=project_leader.user.pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

            print(recipients_list)

            # Get Project information
            project = Project.objects.filter(pk=project_pk).first()
            print("PROJECT: ", project)
            if project:
                html_project_title = project.title
                plain_project_name = html2text.html2text(
                    html_project_title
                ).strip()  # nicely rendered html title

                for recipient in recipients_list:
                    if recipient["pk"] == 101073:
                        email_subject = f"SPMS: Project Closed"
                        to_email = [recipient["email"]]

                        template_props = {
                            "email_subject": email_subject,
                            "recipient_name": recipient["name"],
                            "site_url": settings.SITE_URL,
                            "dbca_image_path": get_encoded_image(),
                            "plain_project_name": plain_project_name,
                            "project_id": project_pk,
                        }

                        template_content = render_to_string(templ, template_props)

                        try:
                            send_mail(
                                email_subject,
                                template_content,  # plain text
                                from_email,
                                to_email,
                                fail_silently=False,  # Set this to False to see errors
                                html_message=template_content,
                            )
                        except Exception as e:
                            settings.LOGGER.error(
                                msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                            )
                            return Response(
                                {"error": str(e)},
                                status=HTTP_400_BAD_REQUEST,
                            )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


class DocumentReadyEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Document Ready) for users {req.data['recipients_list']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/document_ready_email.html"

        # Get recipient list
        recipients_list_data = req.data["recipients_list"]  # list of user pks
        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get project information
        project_pk = req.data["project_pk"]
        project = Project.objects.filter(pk=project_pk).first()
        if project:
            html_project_title = project.title
            plain_project_name = html2text.html2text(
                html_project_title
            ).strip()  # nicely rendered html title

            # Get document kind information
            document_kind = req.data["document_kind"]
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            document_kind_as_title = document_kind_dict[document_kind]

            for recipient in recipients_list:
                if recipient["pk"] == 101073:
                    email_subject = f"SPMS: New {document_kind_as_title} Ready"
                    to_email = [recipient["email"]]

                    template_props = {
                        "email_subject": email_subject,
                        "recipient_name": recipient["name"],
                        "project_id": project_pk,
                        "plain_project_name": plain_project_name,
                        "document_type": document_kind,
                        "document_type_title": document_kind_as_title,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    template_content = render_to_string(templ, template_props)

                    try:
                        send_mail(
                            email_subject,
                            template_content,  # plain text
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


class DocumentSentBackEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Document Sent Back) for users {req.data['recipients_list']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/document_sent_back_email.html"
        stage = req.data["stage"]

        # Get recipient list
        recipients_list_data = req.data["recipients_list"]  # list of user pks
        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get project information
        project_pk = req.data["project_pk"]
        project = Project.objects.filter(pk=project_pk).first()
        if project:
            html_project_title = project.title
            plain_project_name = html2text.html2text(
                html_project_title
            ).strip()  # nicely rendered html title

            # Get document kind information
            document_kind = req.data["document_kind"]
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            document_kind_as_title = document_kind_dict[document_kind]

            for recipient in recipients_list:
                if recipient["pk"] == 101073:
                    email_subject = f"SPMS: {document_kind_as_title} Sent Back"
                    to_email = [recipient["email"]]

                    template_props = {
                        "email_subject": email_subject,
                        "recipient_name": recipient["name"],
                        "actioning_user_role": (
                            "directorate" if stage == 3 else "business area lead"
                        ),
                        "project_id": project_pk,
                        "plain_project_name": plain_project_name,
                        "document_type": document_kind,
                        "document_type_title": document_kind_as_title,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    template_content = render_to_string(templ, template_props)

                    try:
                        send_mail(
                            email_subject,
                            template_content,  # plain text
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


class ConceptPlanEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Concept Plan) for users {req.data['recipients_list']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./pdf_templates/conceptplan_web.html"

        # Get recipient list
        recipients_list_data = req.data["recipients_list"]  # list of user pks
        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get project information
        project_pk = req.data["project_pk"]
        project = Project.objects.filter(pk=project_pk).first()
        if project:
            html_project_title = project.title
            plain_project_name = html2text.html2text(
                html_project_title
            ).strip()  # nicely rendered html title

            # Get document kind information
            document_kind = req.data["document_kind"]
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            document_kind_as_title = document_kind_dict[document_kind]

            for recipient in recipients_list:
                if (
                    recipient["pk"] == 101073
                ):  # Change to if settings.DEBUG == True mass replace
                    email_subject = f"SPMS: Concept Plan Review"
                    to_email = [recipient["email"]]

                    template_props = {
                        "email_subject": email_subject,
                        "recipient_name": recipient["name"],
                        "project_id": project_pk,
                        "plain_project_name": plain_project_name,
                        "document_type": document_kind,
                        "document_type_title": document_kind_as_title,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    # template_content = render_to_string(templ, template_props)
                    template_content = render_to_string(templ)

                    try:
                        send_mail(
                            email_subject,
                            template_content,  # plain text
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


class DocumentApprovedEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Document Approved) for users {req.data['recipients_list']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/document_approved_email.html"

        # Get recipient list
        recipients_list_data = req.data["recipients_list"]  # list of user pks
        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get project information
        project_pk = req.data["project_pk"]
        project = Project.objects.filter(pk=project_pk).first()
        if project:
            html_project_title = project.title
            plain_project_name = html2text.html2text(
                html_project_title
            ).strip()  # nicely rendered html title

            # Get document kind information
            document_kind = req.data["document_kind"]
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            document_kind_as_title = document_kind_dict[document_kind]

            for recipient in recipients_list:
                if recipient["pk"] == 101073:
                    email_subject = f"SPMS: {document_kind_as_title} Approved"
                    to_email = [recipient["email"]]

                    template_props = {
                        "email_subject": email_subject,
                        "recipient_name": recipient["name"],
                        "project_id": project_pk,
                        "plain_project_name": plain_project_name,
                        "document_type": document_kind,
                        "document_type_title": document_kind_as_title,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    template_content = render_to_string(templ, template_props)

                    try:
                        send_mail(
                            email_subject,
                            template_content,  # plain text
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


class DocumentRecalledEmail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is attempting to send an email (Document Approved) for users {req.data['recipients_list']}"
        )
        print(req.data)
        # Preset info
        from_email = settings.DEFAULT_FROM_EMAIL
        templ = "./email_templates/document_recalled_email.html"

        # Get recipient list
        recipients_list_data = req.data["recipients_list"]  # list of user pks
        recipients_list = []

        for recipient_pk in recipients_list_data:
            user = User.objects.get(pk=recipient_pk)
            user_name = f"{user.first_name} {user.last_name}"
            user_email = f"{user.email}"
            data_obj = {"pk": user.pk, "name": user_name, "email": user_email}
            recipients_list.append(data_obj)

        # Get project information
        project_pk = req.data["project_pk"]
        project = Project.objects.filter(pk=project_pk).first()
        if project:
            html_project_title = project.title
            plain_project_name = html2text.html2text(
                html_project_title
            ).strip()  # nicely rendered html title

            # Get document kind information
            document_kind = req.data["document_kind"]
            document_kind_dict = {
                "concept": "Science Concept Plan",
                "projectplan": "Science Project Plan",
                "progressreport": "Progress Report",
                "studentreport": "Student Report",
                "projectclosure": "Project Closure",
            }
            document_kind_as_title = document_kind_dict[document_kind]

            actioning_user = User.objects.get(pk=req.user.pk)
            actioning_user_name = (
                f"{actioning_user.first_name} {actioning_user.last_name}"
            )
            actioning_user_email = f"{actioning_user.email}"
            stage = req.data["stage"]

            for recipient in recipients_list:
                if recipient["pk"] == 101073:
                    email_subject = f"SPMS: {document_kind_as_title} Recalled"
                    to_email = [recipient["email"]]

                    template_props = {
                        "user_kind": (
                            "Project Lead" if stage == 2 else "Business Area Lead"
                        ),
                        "email_subject": email_subject,
                        "actioning_user_email": actioning_user_email,
                        "actioning_user_name": actioning_user_name,
                        "recipient_name": recipient["name"],
                        "project_id": project_pk,
                        "plain_project_name": plain_project_name,
                        "document_type": document_kind,
                        "document_type_title": document_kind_as_title,
                        "site_url": settings.SITE_URL,
                        "dbca_image_path": get_encoded_image(),
                    }

                    template_content = render_to_string(templ, template_props)

                    try:
                        send_mail(
                            email_subject,
                            template_content,  # plain text
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
        return Response(
            "Emails Sent!",
            status=HTTP_202_ACCEPTED,
        )


# REPORTS ==========================================================


class DownloadAnnualReport(APIView):
    def get(self, req):
        settings.LOGGER.error(msg=f"{req.user} is downloading annual report")
        pass


class BatchApprove(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.warning(
            msg=f"{req.user} is attempting to batch approve reports..."
        )
        if req.user.is_superuser == False:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        # Get the last report with the highest year
        last_report = AnnualReport.objects.order_by("-year").first()

        # Handle the case where no report is found
        if not last_report:
            return Response(
                {"error": "No annual report found!"},
                status=HTTP_404_NOT_FOUND,
            )

        relevant_docs_belonging_to_last_report_awaiting_final_approval = (
            ProjectDocument.objects.filter(
                Q(kind="studentreport") | Q(kind="progressreport"),
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=True,
            )
            .exclude(
                project__status__in=[
                    "suspended",
                    "terminated",
                    "completed",
                    "closing",
                    "closure_requested",
                ],
            )
            .all()
        )

        try:
            for doc in relevant_docs_belonging_to_last_report_awaiting_final_approval:
                # FIRST ENSURE THEY BELONG TO THE ANNUAL REPORT BY FINDING THE YEAR ON EACH MODEL
                if doc.kind == "studentreport":
                    sr_obj = StudentReport.objects.filter(report=last_report).first()
                    if sr_obj:
                        doc.directorate_approval_granted = True
                        doc.status = "approved"
                        doc.save()
                        project = Project.objects.filter(pk=doc.project.pk).first()
                        project.status = Project.StatusChoices.ACTIVE
                        project.save()

                elif doc.kind == "progressreport":
                    pr_obj = ProgressReport.objects.filter(report=last_report).first()
                    if pr_obj:
                        doc.directorate_approval_granted = True
                        doc.status = "approved"
                        doc.save()
                        project = Project.objects.filter(pk=doc.project.pk).first()
                        project.status = Project.StatusChoices.ACTIVE
                        project.save()

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response(
                str(e),
                HTTP_400_BAD_REQUEST,
            )
        else:
            settings.LOGGER.info(
                msg=f"Reports have been batch approved for year {last_report.year}"
            )
            return Response(
                "Success",
                HTTP_202_ACCEPTED,
            )


class BatchApproveOld(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        settings.LOGGER.warning(
            msg=f"{req.user} is attempting to batch approve older reports..."
        )
        if req.user.is_superuser == False:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        # Get the last report with the highest year
        last_report = AnnualReport.objects.order_by("-year").first()

        # Handle the case where no report is found
        if not last_report:
            return Response(
                {"error": "No annual reports found!"},
                status=HTTP_404_NOT_FOUND,
            )

        relevant_docs_belonging_to_reports_other_than_last_report = (
            ProjectDocument.objects.filter(
                Q(kind="studentreport") | Q(kind="progressreport"),
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=True,
            )
            .exclude(
                project__status__in=["suspended", "terminated", "completed"],
            )
            .all()
        )

        try:
            for doc in relevant_docs_belonging_to_reports_other_than_last_report:
                # FIRST ENSURE THEY BELONG TO THE ANNUAL REPORT BY FINDING THE YEAR ON EACH MODEL
                if doc.kind == "studentreport":
                    sr_obj = StudentReport.objects.filter(document=doc.id).first()
                    # Skip projects with no members
                    if sr_obj and sr_obj.project.members.length == 0:
                        continue
                    if sr_obj and sr_obj.report != last_report:
                        thedoc = sr_obj.document
                    else:
                        # Go to next iteration if belongs to current report
                        continue

                elif doc.kind == "progressreport":
                    pr_obj = ProgressReport.objects.filter(document=doc.id).first()
                    # Skip projects with no members
                    if pr_obj and pr_obj.project.members.length == 0:
                        continue
                    if pr_obj and pr_obj.report != last_report:
                        thedoc = pr_obj.document
                    else:
                        # Go to next iteration if belongs to current report
                        continue

                thedoc.project_lead_approval_granted = True
                thedoc.business_area_lead_approval_granted = True
                thedoc.directorate_approval_granted = True
                thedoc.status = "approved"
                thedoc.save()
                project = Project.objects.filter(pk=thedoc.project.pk).first()
                project.status = Project.StatusChoices.ACTIVE
                project.save()

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response(
                str(e),
                HTTP_400_BAD_REQUEST,
            )
        else:
            settings.LOGGER.info(
                msg=f"Reports have been batch approved for annual report documents before year: {last_report.year}"
            )
            return Response(
                "Success",
                HTTP_202_ACCEPTED,
            )


class NewCycleOpen(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, req):
        print(req.data)
        should_update = req.data["update"]
        should_email = req.data["send_emails"]
        settings.LOGGER.warning(
            msg=f"{req.user} is attempting to batch create new progress reports for latest year {'(Including projects with status Update Requested)' if should_update else '(Active Projects Only)'}..."
        )
        if req.user.is_superuser == False:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        last_report = AnnualReport.objects.order_by("-year").first()

        # Handle the case where no report is found
        if not last_report:
            return Response(
                {"error": "No annual report found!"},
                status=HTTP_404_NOT_FOUND,
            )

        if should_update:
            eligible_projects = Project.objects.filter(
                Q(
                    kind__in=[
                        Project.CategoryKindChoices.SCIENCE,
                        Project.CategoryKindChoices.COREFUNCTION,
                        # Project.CategoryKindChoices.STUDENT,
                    ]
                )
                & Q(status__in=["active", "updating"])
            )
        else:
            eligible_projects = Project.objects.filter(
                Q(
                    kind__in=[
                        Project.CategoryKindChoices.SCIENCE,
                        Project.CategoryKindChoices.COREFUNCTION,
                        # Project.CategoryKindChoices.STUDENT,
                    ]
                )
                & Q(status="active")
            )

        eligible_projects = eligible_projects.exclude(
            documents__progress_report_details__report__year=last_report.year
        )

        if should_update:
            eligible_student_projects = Project.objects.filter(
                Q(status__in=["active", "updating"])
                & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
            )
        else:
            eligible_student_projects = Project.objects.filter(
                Q(status="active") & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
            )

        eligible_student_projects.exclude(
            documents__progress_report_details__report__year=last_report.year
        )

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
                "modifier": req.user.pk,
                "creator": req.user.pk,
                "project": project.pk,
            }

            new_project_document = ProjectDocumentCreateSerializer(data=new_doc_data)

            if new_project_document.is_valid():
                with transaction.atomic():
                    doc = new_project_document.save()
                    if project.kind != Project.CategoryKindChoices.STUDENT:

                        exists = ProgressReport.objects.filter(
                            year=last_report.year, project=project.pk
                        ).exists()

                        if not exists:

                            progress_report_data = {
                                "document": doc.pk,
                                "project": project.pk,
                                "report": last_report.pk,
                                "project": project.pk,
                                "year": last_report.year,
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
                                settings.LOGGER.error(
                                    msg=f"Error validating progress report: {progress_report.errors}"
                                )
                                return Response(
                                    progress_report.errors, HTTP_400_BAD_REQUEST
                                )
                        else:
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                    else:
                        exists = StudentReport.objects.filter(
                            year=last_report.year, project=project.pk
                        ).exists()

                        if not exists:
                            student_report_data = {
                                "document": doc.pk,
                                "project": project.pk,
                                "report": last_report.pk,
                                "project": project.pk,
                                "year": last_report.year,
                                "progress_report": "<p></p>",
                            }

                            student_report = StudentReportCreateSerializer(
                                data=student_report_data
                            )

                            if student_report.is_valid():
                                student_report.save()
                                project.status = Project.StatusChoices.UPDATING
                                project.save()
                            else:
                                print(student_report.errors["non_field_errors"])
                                settings.LOGGER.error(
                                    msg=f"Error validating student report {student_report.errors}"
                                )
                                return Response(
                                    student_report.errors, HTTP_400_BAD_REQUEST
                                )
                        else:
                            project.status = Project.StatusChoices.UPDATING
                            project.save()

            else:
                settings.LOGGER.error(
                    msg=f"Error opening new cycle: {new_project_document.errors}"
                )
                return Response(new_project_document.errors, HTTP_400_BAD_REQUEST)

        if should_email:
            print("Emails should be sent here")
            pass

        return Response(
            HTTP_202_ACCEPTED,
        )


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

        settings.LOGGER.error(
            msg=f"{user} is BATCH Creating PROGRESS/STUDENT reports for eligible projects"
        )
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

    def get_prepopulation_data_from_last_report(self, year):

        data_object = {
            "dm": "",
            "service_delivery_intro": "",
            "research_intro": "",
            "student_intro": "",
            "publications": "",
        }

        # Use the year parameter to search for the first AnnualReport that comes prior to the given year.
        # Whilst this sometimes may be the prior year, sometimes the prior year's report doesnt exist, so just get the year that is closest and which comes before.
        # If there is such a report, prepopulate the data object, otherwise leave it as is.
        # Use the year parameter to find the closest previous report
        previous_year = AnnualReport.objects.filter(year__lt=year).aggregate(
            Max("year")
        )["year__max"]

        if previous_year is not None:
            # If there is a report from the previous year, fetch its data
            previous_report = AnnualReport.objects.get(year=previous_year)
            data_object["dm"] = previous_report.dm
            data_object["service_delivery_intro"] = (
                previous_report.service_delivery_intro
            )
            data_object["research_intro"] = previous_report.research_intro
            data_object["student_intro"] = previous_report.student_intro
            data_object["publications"] = previous_report.publications

        return data_object

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
            "creator": creator,
            "modifier": modifier,
        }

        additional_data = self.get_prepopulation_data_from_last_report(year)

        creation_data.update(additional_data)

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

                # AnnualReportPDF

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

        def delete_student_reports(report):
            reports = StudentReport.objects.filter(report=report).all()
            for report in reports:
                report.document.delete()

        delete_reports(report)
        delete_student_reports(report)
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


class GetReportPDF(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            report_pdf_obj = AnnualReportPDF.objects.get(report=pk)
        except AnnualReportPDF.DoesNotExist:
            raise NotFound
        return report_pdf_obj

    def get(self, req, pk):
        pdf_object = self.go(pk=pk)
        ser = AnnualReportPDFSerializer(
            pdf_object,
        )
        # pdf_data = ser.data.get('pdf_data')
        # Convert the serialized data to a dictionary
        serialized_data = json.loads(json.dumps(ser.data, cls=DjangoJSONEncoder))
        # print(serialized_data)

        # Include the PDF data in the serialized response
        serialized_data["pdf_data"] = ser.data.get("pdf_data")
        return Response(
            serialized_data,
            HTTP_200_OK,
        )


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
        settings.LOGGER.info(
            msg=f"{req.user} is Creating Project Document for project {req.data.get('project')}"
        )
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
                        "aims": (
                            req.data.get("aims")
                            if req.data.get("aims") is not None
                            else "<p></p>"
                        ),
                        "outcome": (
                            req.data.get("outcome")
                            if req.data.get("outcome") is not None
                            else "<p></p>"
                        ),
                        "collaborations": (
                            req.data.get("collaborations")
                            if req.data.get("collaborations") is not None
                            else "<p></p>"
                        ),
                        "strategic_context": (
                            req.data.get("strategic_context")
                            if req.data.get("strategic_context") is not None
                            else "<p></p>"
                        ),
                        "staff_time_allocation": (
                            req.data.get("staff_time_allocation")
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
        </table>'
                        ),
                        "budget": (
                            req.data.get("budget")
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
    </table>'
                        ),
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
                        "background": (
                            req.data.get("background")
                            if req.data.get("background") is not None
                            else "<p></p>"
                        ),
                        "methodology": (
                            req.data.get("methodology")
                            if req.data.get("methodology") is not None
                            else "<p></p>"
                        ),
                        "aims": (
                            req.data.get("aims")
                            if req.data.get("aims") is not None
                            else "<p></p>"
                        ),
                        "outcome": (
                            req.data.get("outcome")
                            if req.data.get("outcome") is not None
                            else "<p></p>"
                        ),
                        "knowledge_transfer": (
                            req.data.get("knowledge_transfer")
                            if req.data.get("knowledge_transfer") is not None
                            else "<p></p>"
                        ),
                        "listed_references": (
                            req.data.get("listed_references")
                            if req.data.get("listed_references") is not None
                            else "<p></p>"
                        ),
                        "operating_budget": (
                            req.data.get("operating_budget")
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
        </table>'
                        ),
                        "operating_budget_external": (
                            req.data.get("operating_budget_external")
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
        </table>'
                        ),
                        "related_projects": (
                            req.data.get("related_projects")
                            if req.data.get("related_projects") is not None
                            else "<p></p>"
                        ),
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
                                    # "bm_endorsement_required": True,
                                    # "hc_endorsement_required": False,
                                    # "dm_endorsement_required": True,
                                    "ae_endorsement_required": False,
                                    # "bm_endorsement_provided": False,
                                    # "hc_endorsement_provided": False,
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
                        "scientific_outputs": (
                            req.data.get("scientific_outputs")
                            if req.data.get("scientific_outputs") is not None
                            else "<p></p>"
                        ),
                        "knowledge_transfer": (
                            req.data.get("knowledge_transfer")
                            if req.data.get("knowledge_transfer") is not None
                            else "<p></p>"
                        ),
                        "data_location": (
                            req.data.get("data_location")
                            if req.data.get("data_location") is not None
                            else "<p></p>"
                        ),
                        "hardcopy_location": (
                            req.data.get("hardcopy_location")
                            if req.data.get("hardcopy_location") is not None
                            else "<p></p>"
                        ),
                        "backup_location": (
                            req.data.get("backup_location")
                            if req.data.get("backup_location") is not None
                            else "<p></p>"
                        ),
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

                    def get_prepopulation_data_from_last_report(year, project):
                        data_object = {
                            "context": "",
                            "aims": "",
                            "progress": "",
                            "implications": "",
                            "future": "",
                        }

                        # Use the year parameter to search for the first ProgressReport that comes prior to the given year.
                        # Whilst this sometimes may be the prior year, sometimes the prior year's report doesnt exist, so just get the year that is closest and which comes before.
                        progress_reports_for_this_project = (
                            ProgressReport.objects.filter(project=project).all()
                        )
                        previous_year = progress_reports_for_this_project.filter(
                            year__lt=year
                        ).aggregate(Max("year"))["year__max"]

                        print(previous_year)

                        if previous_year is not None:
                            # If there is a report from the previous year, fetch its data
                            previous_report = progress_reports_for_this_project.get(
                                year=previous_year
                            )
                            print(previous_report)
                            data_object["context"] = previous_report.context
                            data_object["aims"] = previous_report.aims
                            data_object["progress"] = previous_report.progress
                            data_object["implications"] = previous_report.implications
                            data_object["future"] = previous_report.future

                        return data_object

                    last_reports_data = get_prepopulation_data_from_last_report(
                        year, project
                    )

                    progress_report_data_object = {
                        "document": doc.pk,
                        "report": report_id,
                        "project": project,
                        "year": year,
                        "context": last_reports_data["context"],
                        "implications": last_reports_data["implications"],
                        "future": last_reports_data["future"],
                        "progress": last_reports_data["progress"],
                        "aims": last_reports_data["aims"],
                        "is_final_report": (
                            req.data.get("is_final_report")
                            if req.data.get("is_final_report") is not None
                            else False
                        ),
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

                    def get_prepopulation_data_from_last_report(year, project):
                        data_object = {
                            "progress_report": "",
                        }

                        # Use the year parameter to search for the first ProgressReport that comes prior to the given year.
                        # Whilst this sometimes may be the prior year, sometimes the prior year's report doesnt exist, so just get the year that is closest and which comes before.
                        student_reports_for_this_project = StudentReport.objects.filter(
                            project=project
                        ).all()
                        previous_year = student_reports_for_this_project.filter(
                            year__lt=year
                        ).aggregate(Max("year"))["year__max"]

                        print(previous_year)

                        if previous_year is not None:
                            # If there is a report from the previous year, fetch its data
                            previous_report = student_reports_for_this_project.get(
                                year=previous_year
                            )
                            print(previous_report)
                            data_object["progress_report"] = (
                                previous_report.progress_report
                            )

                        return data_object

                    last_reports_data = get_prepopulation_data_from_last_report(
                        report.year, project
                    )

                    student_report_data_object = {
                        "document": doc.pk,
                        "report": report.pk,
                        "project": project,
                        "year": report.year,
                        "progress_report": last_reports_data["progress_report"],
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


class EndorsementsPendingMyAction(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting endorsements pending action")

        # is_bio = req.user.is_biometrician
        # is_hc = req.user.is_herbarium_curator
        is_aec = req.user.is_aec
        is_superuser = req.user.is_superuser

        documents = []
        aec_input_required = []
        # bm_input_required = []
        # hc_input_required = []

        # Construct Q objects based on conditions
        # q_bm = Q(bm_endorsement_required=True, bm_endorsement_provided=False) & (
        #     Q(bm_endorsement_required=True) if is_bio or is_superuser else Q()
        # )

        # q_hc = Q(hc_endorsement_required=True, hc_endorsement_provided=False) & (
        #     Q(hc_endorsement_required=True) if is_hc or is_superuser else Q()
        # )
        q_ae = Q(ae_endorsement_required=True, ae_endorsement_provided=False) & (
            Q(ae_endorsement_required=True) if is_aec or is_superuser else Q()
        )

        # Filter endorsements based on conditions
        filtered_endorsements = Endorsement.objects.filter(
            # q_bm | q_hc |
            q_ae,
            project_plan__project__status__in=Project.ACTIVE_ONLY,
        )

        for endorsement in filtered_endorsements:
            # if (
            #     endorsement.bm_endorsement_required
            #     and not endorsement.bm_endorsement_provided
            # ):
            #     documents.append(endorsement)
            #     bm_input_required.append(endorsement)

            if (
                endorsement.ae_endorsement_required
                and not endorsement.ae_endorsement_provided
            ):
                documents.append(endorsement)
                aec_input_required.append(endorsement)

            # if (
            #     endorsement.hc_endorsement_required
            #     and not endorsement.hc_endorsement_provided
            # ):
            #     documents.append(endorsement)
            #     hc_input_required.append(endorsement)

        all_aec = MiniEndorsementSerializer(
            aec_input_required if aec_input_required else [],
            many=True,
            context={"request": req},
        ).data

        # all_bm = MiniEndorsementSerializer(
        #     bm_input_required if bm_input_required else [],
        #     many=True,
        #     context={"request": req},
        # ).data

        # all_hc = MiniEndorsementSerializer(
        #     hc_input_required if hc_input_required else [],
        #     many=True,
        #     context={"request": req},
        # ).data

        data = {
            "aec": all_aec,
            # "bm": all_bm,
            # "hc": all_hc,
        }

        return Response(data, status=HTTP_200_OK)


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

        small_user_object = User.objects.filter(pk=req.user.pk).first()

        if small_user_object and small_user_object.work.business_area:
            # user_work = UserWork.objects.get(user=req.user.pk)
            is_directorate = small_user_object.work.business_area.name = (
                "Directorate" or req.user.is_superuser
            )

            active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY).all()

            # Check if the user is a leader of any business area
            business_areas_led = small_user_object.business_areas_led.values_list(
                "id", flat=True
            )
            is_ba_leader = len(business_areas_led) >= 1

            if is_ba_leader:
                # filter further for only projects which the user leads
                ba_projects = active_projects.filter(
                    business_area__pk__in=business_areas_led
                ).all()

                # Extract project IDs for Business Area
                ba_project_ids = ba_projects.values_list("id", flat=True)

                # Fetch all documents requiring BA attention in a single query
                docs_requiring_ba_attention = (
                    ProjectDocument.objects.exclude(
                        status=ProjectDocument.StatusChoices.APPROVED
                    )
                    .filter(
                        project__in=ba_project_ids,
                        project_lead_approval_granted=True,
                        business_area_lead_approval_granted=False,
                    )
                    .all()
                )

                # Append the documents to the respective lists
                documents.extend(docs_requiring_ba_attention)
                ba_input_required.extend(docs_requiring_ba_attention)

            # Directorate Filtering
            if is_directorate:
                # Extract project IDs for Directorate
                directorate_project_ids = active_projects.values_list("id", flat=True)

                # Fetch all documents requiring Directorate attention in a single query
                docs_requiring_directorate_attention = (
                    ProjectDocument.objects.exclude(
                        status=ProjectDocument.StatusChoices.APPROVED
                    )
                    .filter(
                        project__in=directorate_project_ids,
                        business_area_lead_approval_granted=True,
                        directorate_approval_granted=False,
                    )
                    .all()
                )

                # Append the documents to the respective lists
                documents.extend(docs_requiring_directorate_attention)
                directorate_input_required.extend(docs_requiring_directorate_attention)

            # Lead Filtering
            all_leader_memberships = ProjectMember.objects.filter(
                project__in=active_projects, user=small_user_object, is_leader=True
            ).select_related("project")

            # Extract project IDs for projects where the user is a lead
            lead_project_ids = [
                membership.project_id for membership in all_leader_memberships
            ]

            # Fetch all documents requiring lead attention in a single query
            docs_requiring_lead_attention = (
                ProjectDocument.objects.exclude(
                    status=ProjectDocument.StatusChoices.APPROVED
                )
                .filter(
                    project__in=lead_project_ids,
                    project_lead_approval_granted=False,
                )
                .all()
            )

            # Separate the documents based on lead and member input
            for doc in docs_requiring_lead_attention:
                documents.append(doc)
                if doc.project_id in lead_project_ids:
                    pl_input_required.append(doc)
                else:
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
        else:
            data = {"all": [], "team": [], "lead": [], "ba": [], "directorate": []}
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


class UpdateStudentReport(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            report = StudentReport.objects.filter(document=pk).first()
        except StudentReport.DoesNotExist:
            raise NotFound
        return report

    def post(self, req):
        report = self.go(pk=int(req.data["main_document_pk"]))
        # report.progress_report = req.data["html"]
        # report.save()
        # ser = StudentReportSerializer(report)

        ser = StudentReportSerializer(
            report,
            data={"progress_report": req.data["html"]},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            up_ser = StudentReportSerializer(updated)
            return Response(
                up_ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class UpdateProgressReport(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            report = ProgressReport.objects.filter(document=pk).first()
        except ProgressReport.DoesNotExist:
            raise NotFound
        return report

    def post(self, req):
        report = self.go(pk=int(req.data["main_document_pk"]))
        section = req.data["section"]
        html_data = req.data["html"]
        # report.progress_report = req.data["html"]
        # report.save()
        # ser = StudentReportSerializer(report)

        ser = ProgressReportSerializer(
            report,
            data={f"{section}": html_data},
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            up_ser = ProgressReportSerializer(updated)
            return Response(
                up_ser.data,
                HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
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


class FinalDocApproval(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_document(self, pk):
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req):
        kind = req.data.get("kind")
        reportPk = req.data.get("reportPk")
        documentPk = req.data.get("documentPk")
        isActive = req.data.get("isActive")
        print(req.data)

        if isActive == False:
            settings.LOGGER.info(
                msg=f"{req.user} is providing final approval for {documentPk}"
            )
            # print({kind, reportPk, documentPk})
            # return Response({"error": True}, HTTP_400_BAD_REQUEST)
            document = self.get_document(pk=documentPk)

            data = {
                "project_lead_approval_granted": True,
                "business_area_lead_approval_granted": True,
                "directorate_approval_granted": True,
                "modifier": req.user.pk,
                "status": "approved",
            }
            ser = ProjectDocumentSerializer(
                document,
                data=data,
                partial=True,
            )
            if ser.is_valid():
                u_document = ser.save()
                u_document.project.status = Project.StatusChoices.ACTIVE
                u_document.project.save()
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )
            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        elif isActive == True:
            settings.LOGGER.info(
                msg=f"{req.user} is recalling final approval for docID: {documentPk}"
            )
            # print({kind, reportPk, documentPk})
            # return Response({"error": True}, HTTP_400_BAD_REQUEST)
            document = self.get_document(pk=documentPk)

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
                u_document.project.status = Project.StatusChoices.UPDATING
                u_document.project.save()
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )
            return Response(
                TinyProjectDocumentSerializer(u_document).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            print("Noned")
            return Response(
                {"error": "Something went wrong!"},
                status=HTTP_400_BAD_REQUEST,
            )


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
        # document_kind = document.kind

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

            # If stage 3
            if u_document.kind == "concept" and (stage == 3 or stage == "3"):
                # Create a fresh document with type of project plan =====================
                # Get the project id
                project_pk = document.project.pk
                kind = "projectplan"
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
                        projplanmaindoc = document_serializer.save()
                        # Create a project plan

                        project_plan_data_object = {
                            "document": projplanmaindoc.pk,
                            "project": project_pk,
                            "background": "<p></p>",
                            "methodology": "<p></p>",
                            "aims": "<p></p>",
                            "outcome": "<p></p>",
                            "knowledge_transfer": "<p></p>",
                            "listed_references": "<p></p>",
                            "operating_budget": '<table class="table-light">\
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
                            "operating_budget_external": '<table class="table-light">\
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
                            "related_projects": "<p></p>",
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
                                        # "bm_endorsement_required": True,
                                        # "hc_endorsement_required": False,
                                        # "dm_endorsement_required": True,
                                        "ae_endorsement_required": False,
                                        # "bm_endorsement_provided": False,
                                        # "hc_endorsement_provided": False,
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
                            u_document.project.status = Project.StatusChoices.PENDING
                            u_document.project.save()
                        else:
                            settings.LOGGER.error(
                                msg=f"{project_plan_serializer.errors}"
                            )
                            return Response(
                                project_plan_serializer.errors,
                                status=HTTP_400_BAD_REQUEST,
                            )

                else:
                    settings.LOGGER.error(msg=f"{document_serializer.errors}")
                    return Response(
                        document_serializer.errors,
                        HTTP_400_BAD_REQUEST,
                    )

            if u_document.kind == "projectplan" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.UPDATING
                u_document.project.save()
            if u_document.kind == "progressreport" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.ACTIVE
                u_document.project.save()
            if u_document.kind == "studentreport" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.ACTIVE
                u_document.project.save()
            if u_document.kind == "projectclosure" and (stage == 3 or stage == "3"):
                settings.LOGGER.info(msg=f"{req.user} is closing a project")
                # find the closure matching
                closure_doc = ProjectClosure.objects.get(document=u_document)
                outcome = closure_doc.intended_outcome
                # if outcome == "force_completed":
                #     outcome = "completed"
                u_document.project.status = outcome
                u_document.project.save()

            # Send Emails
            should_send_email = req.data["shouldSendEmail"]

            if should_send_email:
                # if settings.DEBUG == False:
                if u_document.kind == "concept":
                    if stage == 1:
                        pass
                    if stage == 2:
                        pass
                    if stage == 3:
                        pass
                elif u_document.kind == "projectplan":
                    if stage == 1:
                        pass
                    if stage == 2:
                        pass
                    if stage == 3:
                        pass
                elif u_document.kind == "progressreport":
                    if stage == 1:
                        pass
                    if stage == 2:
                        pass
                    if stage == 3:
                        pass
                elif u_document.kind == "studentreport":
                    if stage == 1:
                        pass
                    if stage == 2:
                        pass
                    if stage == 3:
                        pass
                elif u_document.kind == "projectclosure":
                    if stage == 1:
                        pass
                    if stage == 2:
                        pass
                    if stage == 3:
                        pass

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

            elif u_document.kind == "progressreport" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.UPDATING
                u_document.project.save()

            elif u_document.kind == "studentreport" and (stage == 3 or stage == "3"):
                u_document.project.status = Project.StatusChoices.UPDATING
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


class DeleteAECEndorsement(APIView):
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
        settings.LOGGER.info(
            msg=f"{req.user} is deleting aec endorsement and pdf for project plan {project_plan} with db object {endorsement}"
        )

        # First update the endorsement to remove approved
        end_ser = EndorsementSerializer(
            endorsement,
            data={"ae_endorsement_provided": False},
            partial=True,
        )

        if end_ser.is_valid():
            with transaction.atomic():
                # Update
                updated = end_ser.save()
                # Next delete the pdf
                pdf_obj = AECEndorsementPDF.objects.filter(
                    endorsement=endorsement
                ).first()
                if pdf_obj:
                    pdf_obj.delete()

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
        settings.LOGGER.info(msg=f"{req.user} is updating publication {pk}")
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
