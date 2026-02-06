"""
Notification views - Admin notification operations
"""

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.core.cache import cache
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
import requests

from ..models import (
    ProjectDocument,
    AnnualReport,
    ProgressReport,
    StudentReport,
    CustomPublication,
)
from projects.models import Project
from agencies.models import BusinessArea
from users.models import User, PublicStaffProfile
from ..serializers import (
    ProjectDocumentCreateSerializer,
    ProgressReportCreateSerializer,
    StudentReportCreateSerializer,
    CustomPublicationSerializer,
    LibraryPublicationResponseSerializer,
    PublicationResponseSerializer,
)
from ..utils.helpers import get_current_maintainer_id, get_encoded_image
from config.helpers import send_email_with_embedded_image


class NewCycleOpen(APIView):
    """
    Open new reporting cycle and create progress/student reports for eligible projects
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        should_update = request.data["update"]
        should_prepopulate = request.data["prepopulate"]
        should_email = request.data["send_emails"]

        settings.LOGGER.warning(
            f"{request.user} is attempting to batch create new progress reports for latest year "
            f"{'(Including projects with status Update Requested)' if should_update else '(Active Projects Only)'}..."
        )

        if not request.user.is_superuser:
            return Response(
                {"error": "You don't have permission to do that!"},
                HTTP_401_UNAUTHORIZED,
            )

        last_report = AnnualReport.objects.order_by("-year").first()

        if not last_report:
            return Response(
                {"error": "No annual report found!"},
                status=HTTP_404_NOT_FOUND,
            )

        # Get eligible science/core function projects
        if should_update:
            eligible_projects = Project.objects.filter(
                Q(
                    kind__in=[
                        Project.CategoryKindChoices.SCIENCE,
                        Project.CategoryKindChoices.COREFUNCTION,
                    ]
                )
                & Q(status__in=["active", "updating", "suspended"])
            )
        else:
            eligible_projects = Project.objects.filter(
                Q(
                    kind__in=[
                        Project.CategoryKindChoices.SCIENCE,
                        Project.CategoryKindChoices.COREFUNCTION,
                    ]
                )
                & Q(status="active")
            )

        eligible_projects = eligible_projects.exclude(
            documents__progress_report_details__report__year=last_report.year
        )

        # Get eligible student projects
        if should_update:
            eligible_student_projects = Project.objects.filter(
                Q(status__in=["active", "updating", "suspended"])
                & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
            )
        else:
            eligible_student_projects = Project.objects.filter(
                Q(status="active") & Q(kind__in=[Project.CategoryKindChoices.STUDENT])
            )

        eligible_student_projects = eligible_student_projects.exclude(
            documents__student_report_details__report__year=last_report.year
        )

        # Combine querysets
        all_eligible_projects = eligible_projects | eligible_student_projects

        # Create documents for each eligible project
        for project in all_eligible_projects:
            if project.kind == Project.CategoryKindChoices.STUDENT:
                typeofdoc = ProjectDocument.CategoryKindChoices.STUDENTREPORT
            elif project.kind in [
                Project.CategoryKindChoices.SCIENCE,
                Project.CategoryKindChoices.COREFUNCTION,
            ]:
                typeofdoc = ProjectDocument.CategoryKindChoices.PROGRESSREPORT
            else:
                continue

            new_doc_data = {
                "kind": typeofdoc,
                "status": "new",
                "modifier": request.user.pk,
                "creator": request.user.pk,
                "project": project.pk,
            }

            new_project_document = ProjectDocumentCreateSerializer(data=new_doc_data)

            if new_project_document.is_valid():
                with transaction.atomic():
                    doc = new_project_document.save()

                    if project.kind != Project.CategoryKindChoices.STUDENT:
                        # Create progress report
                        exists = ProgressReport.objects.filter(
                            year=last_report.year, project=project.pk
                        ).exists()

                        if not exists:
                            # Get previous report for prepopulation
                            last_one = (
                                ProgressReport.objects.filter(project=project.pk)
                                .order_by("-year")
                                .first()
                            )

                            if not should_prepopulate:
                                # Prepopulate only aims, context, implications
                                prepopulated_aims = (
                                    last_one.aims if last_one else "<p></p>"
                                )
                                prepopulated_context = (
                                    last_one.context if last_one else "<p></p>"
                                )
                                prepopulated_implications = (
                                    last_one.implications if last_one else "<p></p>"
                                )

                                progress_report_data = {
                                    "document": doc.pk,
                                    "project": project.pk,
                                    "report": last_report.pk,
                                    "year": last_report.year,
                                    "context": prepopulated_context,
                                    "implications": prepopulated_implications,
                                    "future": "<p></p>",
                                    "progress": "<p></p>",
                                    "aims": prepopulated_aims,
                                }
                            else:
                                # Prepopulate with all last year's data
                                if last_one:
                                    progress_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
                                        "year": last_report.year,
                                        "context": last_one.context,
                                        "implications": last_one.implications,
                                        "future": last_one.future,
                                        "progress": last_one.progress,
                                        "aims": last_one.aims,
                                    }
                                else:
                                    progress_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
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
                                    f"Error validating progress report: {progress_report.errors}"
                                )
                                return Response(
                                    progress_report.errors, HTTP_400_BAD_REQUEST
                                )
                        else:
                            project.status = Project.StatusChoices.UPDATING
                            project.save()
                    else:
                        # Create student report
                        exists = StudentReport.objects.filter(
                            year=last_report.year, project=project.pk
                        ).exists()

                        if not exists:
                            # Get previous report for prepopulation
                            last_one = (
                                StudentReport.objects.filter(project=project.pk)
                                .order_by("-year")
                                .first()
                            )

                            if not should_prepopulate:
                                student_report_data = {
                                    "document": doc.pk,
                                    "project": project.pk,
                                    "report": last_report.pk,
                                    "year": last_report.year,
                                    "progress_report": "<p></p>",
                                }
                            else:
                                # Prepopulate with last year's data
                                if last_one:
                                    student_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
                                        "year": last_report.year,
                                        "progress_report": last_one.progress_report,
                                    }
                                else:
                                    student_report_data = {
                                        "document": doc.pk,
                                        "project": project.pk,
                                        "report": last_report.pk,
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
                                settings.LOGGER.error(
                                    f"Error validating student report {student_report.errors}"
                                )
                                return Response(
                                    student_report.errors, HTTP_400_BAD_REQUEST
                                )
                        else:
                            project.status = Project.StatusChoices.UPDATING
                            project.save()

            else:
                settings.LOGGER.error(
                    f"Error opening new cycle: {new_project_document.errors}"
                )
                return Response(new_project_document.errors, HTTP_400_BAD_REQUEST)

        # Send emails if requested
        if should_email:
            settings.LOGGER.info("Sending cycle opened emails")
            maintainer_id = get_current_maintainer_id()
            from_email = settings.DEFAULT_FROM_EMAIL
            template_path = "./email_templates/new_cycle_open_email.html"

            actioning_user = User.objects.get(pk=request.user.pk)
            actioning_user_name = f"{actioning_user.display_first_name} {actioning_user.display_last_name}"
            actioning_user_email = actioning_user.email

            financial_year_string = f"{int(last_report.year-1)}-{int(last_report.year)}"

            # Get business area leaders
            recipients_list = []
            bas = BusinessArea.objects.all()
            for ba in bas:
                ba_lead = ba.leader
                if ba_lead and ba_lead.is_active and ba_lead.is_staff:
                    data_obj = {
                        "pk": ba_lead.pk,
                        "name": f"{ba_lead.display_first_name} {ba_lead.display_last_name}",
                        "email": ba_lead.email,
                    }
                    recipients_list.append(data_obj)

            processed = []
            for recipient in recipients_list:
                if recipient["pk"] not in processed:
                    if settings.ENVIRONMENT == "production":
                        settings.LOGGER.info(
                            f"PRODUCTION: Sending email to {recipient['name']}"
                        )

                        email_subject = "SPMS: New Reporting Cycle Open"
                        to_email = [recipient["email"]]

                        template_props = {
                            "email_subject": email_subject,
                            "actioning_user_email": actioning_user_email,
                            "actioning_user_name": actioning_user_name,
                            "financial_year_string": financial_year_string,
                            "recipient_name": recipient["name"],
                            "site_url": settings.SITE_URL,
                            "dbca_image_path": get_encoded_image(),
                        }

                        template_content = render_to_string(
                            template_path, template_props
                        )

                        try:
                            send_email_with_embedded_image(
                                recipient_email=to_email,
                                subject=email_subject,
                                html_content=template_content,
                            )
                        except Exception as e:
                            settings.LOGGER.error(f"Email Error: {e}")
                            return Response(
                                {"error": str(e)},
                                status=HTTP_400_BAD_REQUEST,
                            )
                    else:
                        # Test environment - only send to maintainer
                        if recipient["pk"] == maintainer_id:
                            settings.LOGGER.info(
                                f"TEST: Sending email to {recipient['name']}"
                            )

                            email_subject = "SPMS: New Reporting Cycle Open"
                            to_email = [recipient["email"]]

                            template_props = {
                                "email_subject": email_subject,
                                "actioning_user_email": actioning_user_email,
                                "actioning_user_name": actioning_user_name,
                                "financial_year_string": financial_year_string,
                                "recipient_name": recipient["name"],
                                "site_url": settings.SITE_URL,
                                "dbca_image_path": get_encoded_image(),
                            }

                            template_content = render_to_string(
                                template_path, template_props
                            )

                            try:
                                send_email_with_embedded_image(
                                    recipient_email=to_email,
                                    subject=email_subject,
                                    html_content=template_content,
                                )
                            except Exception as e:
                                settings.LOGGER.error(f"Email Error: {e}")
                                return Response(
                                    {"error": str(e)},
                                    status=HTTP_400_BAD_REQUEST,
                                )
                    processed.append(recipient["pk"])

            return Response("Emails Sent!", status=HTTP_202_ACCEPTED)

        return Response(status=HTTP_202_ACCEPTED)


class SendBumpEmails(APIView):
    """
    Send reminder emails for documents requiring action
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        documents_requiring_action = request.data.get("documentsRequiringAction", [])

        if not documents_requiring_action:
            return Response(
                {"error": "No documents provided"},
                status=HTTP_400_BAD_REQUEST,
            )

        settings.LOGGER.warning(
            f"{request.user} is sending bump emails for {len(documents_requiring_action)} documents..."
        )

        template_path = "./email_templates/bump_email.html"

        actioning_user = User.objects.get(pk=request.user.pk)
        actioning_user_name = (
            f"{actioning_user.display_first_name} {actioning_user.display_last_name}"
        )
        actioning_user_email = actioning_user.email

        # Document kind mapping
        document_kind_dict = {
            "concept": "Concept Plan",
            "projectplan": "Project Plan",
            "progressreport": "Progress Report",
            "studentreport": "Student Report",
            "projectclosure": "Project Closure",
        }

        def determine_doc_kind_url_string(kind):
            url_mapping = {
                "concept": "concept",
                "projectplan": "project",
                "progressreport": "progress",
                "studentreport": "student",
                "projectclosure": "closure",
            }
            return url_mapping.get(kind, kind)

        emails_sent = 0
        errors = []

        for doc_data in documents_requiring_action:
            try:
                user_to_action = User.objects.get(pk=doc_data.get("userToTakeAction"))

                if (
                    not user_to_action.is_active
                    or not user_to_action.email
                    or not user_to_action.is_staff
                ):
                    errors.append(
                        f"User {user_to_action.display_first_name} {user_to_action.display_last_name} "
                        f"is inactive, external or has no email"
                    )
                    continue

                document_kind_raw = doc_data.get("documentKind")
                document_kind_title = document_kind_dict.get(
                    document_kind_raw, document_kind_raw
                )
                url_doc_kind = determine_doc_kind_url_string(document_kind_raw)

                email_subject = (
                    f"SPMS: Action Required - {doc_data.get('projectTitle')}"
                )
                to_email = [user_to_action.email]

                template_props = {
                    "email_subject": email_subject,
                    "actioning_user_email": actioning_user_email,
                    "actioning_user_name": actioning_user_name,
                    "recipient_name": f"{user_to_action.display_first_name} {user_to_action.display_last_name}",
                    "recipient_email": user_to_action.email,
                    "project_title": doc_data.get("projectTitle"),
                    "project_id": doc_data.get("projectId"),
                    "document_kind": document_kind_title,
                    "document_kind_raw": document_kind_raw,
                    "action_capacity": doc_data.get("actionCapacity"),
                    "site_url": settings.SITE_URL,
                    "document_url": f"{settings.SITE_URL}/projects/{doc_data.get('projectId')}/{url_doc_kind}",
                }

                template_content = render_to_string(template_path, template_props)

                if settings.ENVIRONMENT == "production":
                    settings.LOGGER.info(
                        f"PRODUCTION: Sending bump email to {user_to_action.email}"
                    )

                    try:
                        send_email_with_embedded_image(
                            recipient_email=to_email,
                            subject=email_subject,
                            html_content=template_content,
                        )
                        emails_sent += 1
                    except Exception as email_error:
                        settings.LOGGER.error(f"Email Error: {email_error}")
                        errors.append(
                            f"Failed to send email to {user_to_action.email}: {str(email_error)}"
                        )
                else:
                    # Test environment - only send to maintainer
                    maintainer_id = get_current_maintainer_id()
                    if user_to_action.pk == maintainer_id:
                        settings.LOGGER.info(
                            f"TEST: Sending bump email to {user_to_action.email}"
                        )

                        try:
                            send_email_with_embedded_image(
                                recipient_email=to_email,
                                subject=email_subject,
                                html_content=template_content,
                            )
                            emails_sent += 1
                        except Exception as email_error:
                            settings.LOGGER.error(f"Email Error: {email_error}")
                            errors.append(
                                f"Failed to send email to {user_to_action.email}: {str(email_error)}"
                            )
                    else:
                        settings.LOGGER.info(
                            f"TEST: Skipping email to {user_to_action.email} (not maintainer)"
                        )

            except User.DoesNotExist:
                errors.append(
                    f"User with ID {doc_data.get('userToTakeAction')} not found"
                )
            except Project.DoesNotExist:
                errors.append(f"Project with ID {doc_data.get('projectId')} not found")
            except Exception as e:
                settings.LOGGER.error(
                    f"Unexpected error processing document {doc_data.get('documentId')}: {str(e)}"
                )
                errors.append(
                    f"Error processing document {doc_data.get('documentId')}: {str(e)}"
                )

        response_data = {
            "emails_sent": emails_sent,
            "total_documents": len(documents_requiring_action),
        }

        if errors:
            response_data["errors"] = errors
            settings.LOGGER.warning(
                f"Bump emails completed with {len(errors)} errors: {errors}"
            )

        if emails_sent > 0:
            settings.LOGGER.info(f"Successfully sent {emails_sent} bump emails")
            return Response(response_data, status=HTTP_200_OK)
        else:
            return Response(
                {"error": "No emails were sent", "details": errors},
                status=HTTP_400_BAD_REQUEST,
            )


class UserPublications(APIView):
    """
    Get user publications from library API and custom publications
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def _error_response(self, message):
        return Response(
            {
                "staffProfilePk": 0,
                "libraryData": {
                    "numFound": 0,
                    "start": 0,
                    "numFoundExact": True,
                    "docs": [],
                    "isError": True,
                    "errorMessage": message,
                },
                "customPublications": [],
            },
            status=HTTP_200_OK,
        )

    def _get_library_publications(self, employee_id):
        api_url = f"{settings.LIBRARY_API_URL}{employee_id}&rows=1000"
        token = settings.LIBRARY_BEARER_TOKEN.replace("Bearer ", "")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            settings.LOGGER.error(
                f"Failed to retrieve data from API:\n{response.status_code}: {response.text}"
            )
            raise Exception(f"API request failed with status {response.status_code}")

        return response.json()

    def get(self, request, employee_id):
        settings.LOGGER.info(
            f"{request.user} is getting UserPublications for {employee_id}"
        )

        if not employee_id or employee_id == "null":
            return self._error_response("No employee ID provided")

        if not settings.LIBRARY_API_URL:
            return self._error_response("Library API configuration missing")

        if not settings.LIBRARY_BEARER_TOKEN:
            return self._error_response("Library Token configuration missing")

        # Check cache
        cache_key = f"user_publications_{employee_id}"
        cached_data = cache.get(cache_key)

        # Get staff profile
        staff_profile = PublicStaffProfile.objects.filter(
            employee_id=employee_id
        ).first()

        # Get custom publications
        custom_publications = CustomPublication.objects.filter(
            public_profile__employee_id=employee_id
        ).all()

        if cached_data:
            settings.LOGGER.info(f"Returning cached publications for {employee_id}")
            response_data = {
                "staffProfilePk": staff_profile.pk if staff_profile else 0,
                "libraryData": cached_data,
                "customPublications": CustomPublicationSerializer(
                    custom_publications, many=True
                ).data,
            }
            return Response(response_data, status=HTTP_200_OK)

        try:
            # Get library publications
            library_data = self._get_library_publications(employee_id)

            library_response = {
                "numFound": library_data.get("response", {}).get("numFound", 0),
                "start": library_data.get("response", {}).get("start", 0),
                "numFoundExact": library_data.get("response", {}).get(
                    "numFoundExact", True
                ),
                "docs": library_data.get("response", {}).get("docs", []),
                "isError": False,
                "errorMessage": "",
            }

            # Serialize and cache
            library_serializer = LibraryPublicationResponseSerializer(
                data=library_response
            )
            if not library_serializer.is_valid():
                settings.LOGGER.error(
                    f"Library Serializer errors: {library_serializer.errors}"
                )
                return self._error_response("Invalid library data format")

            cache.set(
                cache_key,
                library_serializer.data,
                timeout=timedelta(hours=24).total_seconds(),
            )

            response_data = {
                "staffProfilePk": staff_profile.pk if staff_profile else 0,
                "libraryData": library_serializer.data,
                "customPublications": CustomPublicationSerializer(
                    custom_publications, many=True
                ).data,
            }

            final_serializer = PublicationResponseSerializer(data=response_data)
            if not final_serializer.is_valid():
                settings.LOGGER.error(
                    f"Final Serializer errors: {final_serializer.errors}"
                )
                return self._error_response("Invalid response format")

            return Response(final_serializer.data, status=HTTP_200_OK)

        except Exception as e:
            settings.LOGGER.error(f"Error processing request: {str(e)}")
            return self._error_response("Failed to process request")


class SendMentionNotification(APIView):
    """
    Send email notifications to mentioned users in document comments
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            document_id = request.data.get("documentId")
            project_id = request.data.get("projectId")
            commenter = request.data.get("commenter")
            mentioned_users = request.data.get("mentionedUsers", [])
            comment_content = request.data.get("commentContent", "")

            # Fetch document and project
            try:
                document = ProjectDocument.objects.get(pk=document_id)
                project = Project.objects.get(pk=project_id)
                project_tag = project.get_project_tag()
            except (ProjectDocument.DoesNotExist, Project.DoesNotExist) as e:
                settings.LOGGER.error(f"Document or Project not found: {e}")
                return Response(
                    {"error": "Document or Project not found"},
                    status=HTTP_404_NOT_FOUND,
                )

            # Generate document URL
            url_safe_kind_dict = {
                "concept": "concept",
                "projectplan": "project",
                "progressreport": "progress",
                "studentreport": "student",
                "projectclosure": "closure",
            }

            document_url = f"{settings.SITE_URL}/projects/{project.pk}/{url_safe_kind_dict[document.kind]}"

            # Clean comment content
            def clean_comment_content(html_content):
                from bs4 import BeautifulSoup

                if not html_content:
                    return ""

                try:
                    soup = BeautifulSoup(html_content, "html.parser")
                    mention_spans = soup.find_all(
                        "span", {"data-lexical-mention": "true"}
                    )
                    for span in mention_spans:
                        span.replace_with(span.get_text())
                    return soup.get_text().strip()
                except Exception as e:
                    settings.LOGGER.error(f"Error cleaning comment content: {e}")
                    return html_content

            cleaned_comment = clean_comment_content(comment_content)

            if not mentioned_users:
                return Response(
                    {
                        "message": "No mentioned users found - no emails sent",
                        "recipients": 0,
                        "mentioned_users": 0,
                    },
                    status=HTTP_200_OK,
                )

            # Process mentioned users
            recipients_to_notify = []
            for user_data in mentioned_users:
                user_id = user_data.get("id")
                user_name = user_data.get("name")
                user_email = user_data.get("email")

                if user_email and user_email.endswith("@dbca.wa.gov.au"):
                    try:
                        user = User.objects.get(pk=user_id)
                        if user.is_active and user.is_staff:
                            recipients_to_notify.append(
                                {"id": user_id, "name": user_name, "email": user_email}
                            )
                    except User.DoesNotExist:
                        settings.LOGGER.warning(f"Mentioned user {user_id} not found")
                        continue

            # Send emails
            processed_users = set()
            emails_sent = 0

            for recipient in recipients_to_notify:
                user_id = recipient.get("id")
                user_name = recipient.get("name")
                user_email = recipient.get("email")

                if user_id in processed_users:
                    continue

                processed_users.add(user_id)

                # Skip if not in production and not test user
                maintainer_id = get_current_maintainer_id()
                if (settings.ENVIRONMENT != "production") and user_id != maintainer_id:
                    settings.LOGGER.info(
                        f"TEST: Skipping mention notification to {user_name}"
                    )
                    continue

                to_email = [user_email]
                document_kind_string_readable = ProjectDocument.CategoryKindChoices(
                    document.kind
                ).label

                email_subject = f"SPMS: You were mentioned in a comment on {document_kind_string_readable} ({project_tag})"

                template_props = {
                    "recipient_name": user_name,
                    "commenter_name": commenter.get("name"),
                    "document_type_title": document_kind_string_readable,
                    "project_tag": project_tag,
                    "project_name": project.title,
                    "document_url": document_url,
                    "comment_content": cleaned_comment,
                    "is_mention": True,
                    "site_url": settings.SITE_URL,
                }

                try:
                    template_content = render_to_string(
                        "./email_templates/document_comment_mention.html",
                        template_props,
                    )
                    send_email_with_embedded_image(
                        recipient_email=to_email,
                        subject=email_subject,
                        html_content=template_content,
                    )
                    emails_sent += 1
                    settings.LOGGER.info(
                        f"{'PRODUCTION' if settings.ENVIRONMENT == 'production' else 'TEST'}: "
                        f"Sent comment notification to {user_name}"
                    )
                except Exception as e:
                    settings.LOGGER.error(f"Comment Notification Email Error: {e}")

            return Response(
                {
                    "message": f"Mention notifications sent to {emails_sent} users",
                    "recipients": len(recipients_to_notify),
                    "mentioned_users": len(mentioned_users),
                },
                status=HTTP_200_OK,
            )

        except Exception as e:
            settings.LOGGER.error(f"Error sending comment notifications: {str(e)}")
            return Response({"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)
