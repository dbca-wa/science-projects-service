"""
Document admin views
"""
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from projects.models import Project, ProjectMember
from users.models import User
from ..models import (
    ProjectDocument,
    # Comment,  # TODO: Comment model not yet implemented
    AnnualReport,
    StudentReport,
    ProgressReport,
)
from ..serializers import (
    TinyProjectDocumentSerializer,
    # TinyCommentSerializer,  # TODO: Comment serializers not yet implemented
    # TinyCommentCreateSerializer,
    ProjectDocumentSerializer,
)
from ..utils.helpers import extract_text_content


class ProjectDocsPendingMyActionAllStages(APIView):
    """Get all documents pending user action across all approval stages"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get documents pending action for current user"""
        settings.LOGGER.info(
            msg=f"{request.user} is getting their documents pending action"
        )
        
        documents = []
        member_input_required = []
        pl_input_required = []
        ba_input_required = []
        directorate_input_required = []

        # Optimize query with select_related
        small_user_object = (
            User.objects.filter(pk=request.user.pk)
            .select_related("work", "work__business_area")
            .prefetch_related("business_areas_led")
            .first()
        )

        if small_user_object:
            # Handle users without work relationship
            ba = getattr(small_user_object, 'work', None)
            ba = ba.business_area if ba else None
            is_directorate = (
                ba != None and ba.name == "Directorate"
            ) or request.user.is_superuser

            active_projects = Project.objects.exclude(status__in=Project.CLOSED_ONLY).all()

            # Check if the user is a leader of any business area
            business_areas_led = small_user_object.business_areas_led.values_list(
                "id", flat=True
            )

            is_ba_leader = len(business_areas_led) >= 1

            if is_ba_leader:
                # Filter for projects which the user leads
                ba_projects = active_projects.filter(
                    business_area__pk__in=business_areas_led
                ).all()

                # Extract project IDs for Business Area
                ba_project_ids = ba_projects.values_list("id", flat=True)

                # Fetch all documents requiring BA attention with optimized relationships
                docs_requiring_ba_attention = (
                    ProjectDocument.objects.exclude(
                        status=ProjectDocument.StatusChoices.APPROVED
                    )
                    .filter(
                        project__in=ba_project_ids,
                        project_lead_approval_granted=True,
                        business_area_lead_approval_granted=False,
                    )
                    .select_related(
                        "project",
                        "project__business_area",
                        "project__business_area__image",
                        "project__business_area__division",
                        "project__business_area__division__director",
                        "project__business_area__division__approver",
                        "project__business_area__leader",
                        "project__business_area__caretaker",
                        "project__business_area__finance_admin",
                        "project__business_area__data_custodian",
                        "project__image",
                        "project__image__uploader",
                        "pdf",
                        "pdf__document",
                        "pdf__project",
                        "creator",
                        "modifier",
                    )
                    .prefetch_related(
                        "project__business_area__division__directorate_email_list",
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

                # Fetch all documents requiring Directorate attention with optimized relationships
                docs_requiring_directorate_attention = (
                    ProjectDocument.objects.exclude(
                        status=ProjectDocument.StatusChoices.APPROVED
                    )
                    .filter(
                        project__in=directorate_project_ids,
                        business_area_lead_approval_granted=True,
                        directorate_approval_granted=False,
                    )
                    .select_related(
                        "project",
                        "project__business_area",
                        "project__business_area__image",
                        "project__business_area__division",
                        "project__business_area__division__director",
                        "project__business_area__division__approver",
                        "project__business_area__leader",
                        "project__business_area__caretaker",
                        "project__business_area__finance_admin",
                        "project__business_area__data_custodian",
                        "project__image",
                        "project__image__uploader",
                        "pdf",
                        "pdf__document",
                        "pdf__project",
                        "creator",
                        "modifier",
                    )
                    .prefetch_related(
                        "project__business_area__division__directorate_email_list",
                    )
                    .all()
                )

                # Append the documents to the respective lists
                documents.extend(docs_requiring_directorate_attention)
                directorate_input_required.extend(docs_requiring_directorate_attention)

            # Lead Filtering - optimized the membership query
            all_leader_memberships = ProjectMember.objects.filter(
                project__in=active_projects, user=small_user_object, is_leader=True
            ).select_related("project")

            # Extract project IDs for projects where the user is a lead
            lead_project_ids = [
                membership.project_id for membership in all_leader_memberships
            ]

            # Fetch all documents requiring lead attention with optimized relationships
            docs_requiring_lead_attention = (
                ProjectDocument.objects.exclude(
                    status=ProjectDocument.StatusChoices.APPROVED
                )
                .filter(
                    project__in=lead_project_ids,
                    project_lead_approval_granted=False,
                )
                .select_related(
                    "project",
                    "project__business_area",
                    "project__business_area__image",
                    "project__business_area__division",
                    "project__business_area__division__director",
                    "project__business_area__division__approver",
                    "project__business_area__leader",
                    "project__business_area__caretaker",
                    "project__business_area__finance_admin",
                    "project__business_area__data_custodian",
                    "project__image",
                    "project__image__uploader",
                    "pdf",
                    "pdf__document",
                    "pdf__project",
                    "creator",
                    "modifier",
                )
                .prefetch_related(
                    "project__business_area__division__directorate_email_list",
                )
                .all()
            )

            # Separate the documents based on lead and member input
            for doc in docs_requiring_lead_attention:
                documents.append(doc)
                if doc.project_id in lead_project_ids:
                    pl_input_required.append(doc)

            # Optimized this query too (N+1)
            my_non_leader_memberships = (
                ProjectMember.objects.filter(user=request.user, is_leader=False)
                .select_related("project")
                .all()
            )

            my_projects = [
                membership.project for membership in my_non_leader_memberships
            ]

            docs_requiring_team_attention = (
                ProjectDocument.objects.exclude(
                    status=ProjectDocument.StatusChoices.APPROVED
                )
                .filter(project_lead_approval_granted=False, project__in=my_projects)
                .select_related(
                    "project",
                    "project__business_area",
                    "project__business_area__image",
                    "project__business_area__division",
                    "project__business_area__division__director",
                    "project__business_area__division__approver",
                    "project__business_area__leader",
                    "project__business_area__caretaker",
                    "project__business_area__finance_admin",
                    "project__business_area__data_custodian",
                    "project__image",
                    "project__image__uploader",
                    "pdf",
                    "pdf__document",
                    "pdf__project",
                    "creator",
                    "modifier",
                )
                .prefetch_related(
                    "project__business_area__division__directorate_email_list",
                )
                .all()
            )

            for doc in docs_requiring_team_attention:
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
                context={"request": request},
            )

            data = {
                "all": ser.data,
                "team": TinyProjectDocumentSerializer(
                    filtered_pm_input_required,
                    many=True,
                    context={"request": request},
                ).data,
                "lead": TinyProjectDocumentSerializer(
                    filtered_pl_input_required,
                    many=True,
                    context={"request": request},
                ).data,
                "ba": TinyProjectDocumentSerializer(
                    filtered_ba_input_required,
                    many=True,
                    context={"request": request},
                ).data,
                "directorate": TinyProjectDocumentSerializer(
                    filtered_directorate_input_required,
                    many=True,
                    context={"request": request},
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


# TODO: Comment model and serializers not yet implemented
# class ProjectDocumentComments(APIView):
#     """Manage document comments"""
#     
#     permission_classes = [IsAuthenticated]
# 
#     def get(self, request, pk):
#         """Get all comments for a document"""
#         comments = Comment.objects.filter(document_id=pk).all()
#         comments = comments.order_by("-updated_at", "-created_at")
# 
#         ser = TinyCommentSerializer(
#             comments,
#             many=True,
#             context={"request": request},
#         )
#         return Response(
#             ser.data,
#             status=HTTP_200_OK,
#         )
# 
#     def sanitize_html(self, html_content):
#         """
#         Sanitize HTML content while preserving mention data attributes and safely handling CSS
#         """
#         if not html_content:
#             return ""
# 
#         import bleach
#         from bleach.css_sanitizer import CSSSanitizer
# 
#         # Define allowed tags and attributes
#         allowed_tags = [
#             "a",
#             "abbr",
#             "acronym",
#             "b",
#             "blockquote",
#             "code",
#             "em",
#             "i",
#             "li",
#             "ol",
#             "p",
#             "strong",
#             "ul",
#             "br",
#             "div",
#             "span",
#             "h1",
#             "h2",
#             "h3",
#             "h4",
#             "h5",
#             "h6",
#             "table",
#             "thead",
#             "tbody",
#             "tr",
#             "th",
#             "td",
#         ]
# 
#         allowed_attributes = {
#             "*": ["class"],
#             "a": ["href", "title", "target"],
#             "span": [
#                 "data-user-id",
#                 "data-user-email",
#                 "data-user-name",
#                 "data-lexical-mention",
#                 "class",
#                 "style",
#             ],
#             "th": ["colspan", "rowspan"],
#             "td": ["colspan", "rowspan"],
#             "div": ["style"],
#             "p": ["style"],
#         }
# 
#         # Define allowed CSS properties (specifically for mentions)
#         allowed_css_properties = [
#             "background-color",
#             "color",
#             "padding-left",
#             "padding-right",
#             "border-radius",
#             "font-weight",
#         ]
# 
#         # Create a CSS sanitizer with our allowed properties
#         css_sanitizer = CSSSanitizer(
#             allowed_css_properties=allowed_css_properties,
#             allowed_svg_properties=[],
#         )
# 
#         # Clean the HTML while preserving the allowed tags and attributes
#         clean_html = bleach.clean(
#             html_content,
#             tags=allowed_tags,
#             attributes=allowed_attributes,
#             css_sanitizer=css_sanitizer,
#             strip=True,
#         )
# 
#         return clean_html
# 
#     def post(self, request, pk):
#         """Create a new comment on a document"""
#         settings.LOGGER.info(
#             msg=f"{request.user} is trying to post a comment to doc {pk}:\n{extract_text_content(request.data['payload'])}"
#         )
# 
#         sanitized_payload = self.sanitize_html(request.data["payload"])
# 
#         ser = TinyCommentCreateSerializer(
#             data={
#                 "document": pk,
#                 "text": sanitized_payload,
#                 "user": request.data["user"],
#             },
#             context={"request": request},
#         )
#         if ser.is_valid():
#             ser.save()
#             return Response(
#                 ser.data,
#                 status=HTTP_201_CREATED,
#             )
#         else:
#             settings.LOGGER.error(msg=f"FAIL: {ser.errors}")
#             return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class DocumentSpawner(APIView):
    """Spawn a new document for a project"""
    
    def post(self, request):
        """Create a new document"""
        kind = request.kind
        ser = ProjectDocumentSerializer(
            data={"kind": kind, "status": "new", "project": request.project}
        )
        settings.LOGGER.info(msg=f"{request.user} is spawning document")
        if ser.is_valid():
            with transaction.atomic():
                try:
                    project_document = ser.save()
                except Exception as e:
                    settings.LOGGER.error(msg=f"{e}")
                    return Response(e, HTTP_400_BAD_REQUEST)
                else:
                    doc_id = project_document.pk
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
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class GetPreviousReportsData(APIView):
    """Get data from previous reports for prepopulation"""
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Get previous report data for a specific section"""
        project_id = request.data["project_id"]
        doc_kind = request.data["writeable_document_kind"]
        section = request.data["section"]

        if doc_kind == "Progress Report":
            documents_of_type_from_project = ProgressReport.objects.filter(
                project=project_id
            ).order_by("-year")
        elif doc_kind == "Student Report":
            documents_of_type_from_project = StudentReport.objects.filter(
                project=project_id
            ).order_by("-year")
        else:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Check if there are at least two documents (can actually prepopulate with prior data)
        if documents_of_type_from_project.count() < 2:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Get the second-to-last document
        second_last_one = documents_of_type_from_project[1]

        # Get the specified section data
        try:
            section_data = getattr(second_last_one, section)
        except AttributeError:
            return Response(status=HTTP_400_BAD_REQUEST)

        return Response(data=section_data, status=HTTP_200_OK)



class ReopenProject(APIView):
    """Reopen a closed project (fixes typo from RepoenProject)"""
    
    permission_classes = [IsAuthenticated]

    def get_base_document(self, project_id):
        """Get the project closure document"""
        obj = ProjectDocument.objects.filter(
            project=project_id, kind="projectclosure"
        ).first()
        if obj is None:
            return None
        return obj

    def post(self, request, pk):
        """Reopen a project"""
        from ..services.notification_service import NotificationService
        from ..utils.helpers import get_current_maintainer_id
        
        settings.LOGGER.info(
            msg=f"{request.user} is reopening project belonging to doc ({pk})"
        )

        maintainer_id = get_current_maintainer_id()

        with transaction.atomic():
            try:
                settings.LOGGER.info(msg=f"{request.user} is reopening project {pk}")
                project_document = self.get_base_document(pk)

                if project_document == None:
                    project = Project.objects.filter(pk=pk).first()
                    project.status = Project.StatusChoices.UPDATING
                    project.save()
                else:
                    project_document.project.status = "updating"
                    project_document.project.save()
                    project = Project.objects.filter(
                        pk=project_document.project.pk
                    ).first()
                    project_document.delete()
                
                print("SENDING PROJECT REOPENED EMAIL")

                if project:
                    # Send notification via service
                    NotificationService.notify_project_reopened(
                        project=project,
                        reopener=request.user
                    )

                    return Response(
                        "Emails Sent!",
                        status=HTTP_202_ACCEPTED,
                    )
                return Response(status=HTTP_204_NO_CONTENT)
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                return Response(f"{e}", status=HTTP_400_BAD_REQUEST)


class BatchApproveOld(APIView):
    """Batch approve older reports (not from latest year)"""
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Batch approve older reports"""
        settings.LOGGER.warning(
            msg=f"{request.user} is attempting to batch approve older reports..."
        )
        if not request.user.is_superuser:
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

        # Get relevant documents with optimized queries using select_related and prefetch_related
        relevant_docs = (
            ProjectDocument.objects.filter(
                Q(kind="studentreport") | Q(kind="progressreport"),
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=True,
            )
            .exclude(
                project__status__in=["suspended", "terminated", "completed"],
            )
            .select_related("project")
            .prefetch_related(
                "project__members",
                "student_report_details",
                "progress_report_details",
            )
        )

        try:
            # Collect documents and projects that need updating
            docs_to_update = []
            projects_to_update = []

            for doc in relevant_docs:
                should_process = False

                if doc.kind == "studentreport":
                    # Use prefetched data instead of separate query
                    sr_obj = (
                        doc.student_report_details.first()
                        if doc.student_report_details.exists()
                        else None
                    )

                    # Use .count() instead of .length
                    if sr_obj and doc.project.members.count() == 0:
                        continue

                    if sr_obj and sr_obj.report != last_report:
                        should_process = True

                elif doc.kind == "progressreport":
                    # Use prefetched data instead of separate query
                    pr_obj = (
                        doc.progress_report_details.first()
                        if doc.progress_report_details.exists()
                        else None
                    )

                    # Use .count() instead of .length
                    if pr_obj and doc.project.members.count() == 0:
                        continue

                    if pr_obj and pr_obj.report != last_report:
                        should_process = True

                if should_process:
                    # Prepare document for bulk update
                    doc.project_lead_approval_granted = True
                    doc.business_area_lead_approval_granted = True
                    doc.directorate_approval_granted = True
                    doc.status = "approved"
                    docs_to_update.append(doc)

                    # Prepare project for bulk update (avoid duplicate projects)
                    project = doc.project
                    if project not in projects_to_update:
                        project.status = Project.StatusChoices.ACTIVE
                        projects_to_update.append(project)

            # Bulk update documents
            if docs_to_update:
                ProjectDocument.objects.bulk_update(
                    docs_to_update,
                    [
                        "project_lead_approval_granted",
                        "business_area_lead_approval_granted",
                        "directorate_approval_granted",
                        "status",
                    ],
                )

            # Bulk update projects
            if projects_to_update:
                Project.objects.bulk_update(projects_to_update, ["status"])

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


class FinalDocApproval(APIView):
    """Final document approval (no email sent)"""
    
    permission_classes = [IsAuthenticated]

    def get_document(self, pk):
        """Get document by ID"""
        try:
            obj = ProjectDocument.objects.get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound
        return obj

    def post(self, request):
        """Approve or recall final approval"""
        documentPk = request.data.get("documentPk")
        isActive = request.data.get("isActive")

        if isActive == False:
            settings.LOGGER.info(
                msg=f"{request.user} is providing final approval for {documentPk}"
            )
            document = self.get_document(pk=documentPk)

            data = {
                "project_lead_approval_granted": True,
                "business_area_lead_approval_granted": True,
                "directorate_approval_granted": True,
                "modifier": request.user.pk,
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
                msg=f"{request.user} is recalling final approval for docID: {documentPk}"
            )
            document = self.get_document(pk=documentPk)

            data = {
                "directorate_approval_granted": False,
                "modifier": request.user.pk,
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
