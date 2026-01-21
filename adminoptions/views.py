# region IMPORTS ====================================================================================================

from operator import is_, le
from re import A
from tracemalloc import start
from django.conf import settings
from rest_framework.exceptions import (
    NotFound,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction

from adminoptions.models import (
    AdminOptions,
    AdminTask,
    Caretaker,
    ContentField,
    GuideSection,
)
from adminoptions.serializers import (
    AdminOptionsMaintainerSerializer,
    AdminOptionsSerializer,
    AdminTaskRequestCreationSerializer,
    AdminTaskSerializer,
    CaretakerSerializer,
    ContentFieldSerializer,
    GuideSectionCreateUpdateSerializer,
    GuideSectionSerializer,
)
from agencies.models import BusinessArea
from documents.models import ProjectDocument
from documents.serializers import (
    TinyProjectDocumentSerializer,
    TinyProjectDocumentSerializerWithUserDocsBelongTo,
)
from projects.models import Project, ProjectMember
from communications.models import Comment
import users
from users.models import User
from rest_framework import viewsets
from rest_framework.decorators import action

# endregion  =================================================================================================

# region Views ====================================================================================================


class AdminControls(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = AdminOptions.objects.all()
        ser = AdminOptionsSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting an instance of admin controls")
        ser = AdminOptionsSerializer(
            data=req.data,
        )
        if ser.is_valid():
            Controls = ser.save()
            return Response(
                AdminOptionsSerializer(Controls).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class GetMaintainer(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AdminOptions.objects.get(pk=pk)
        except AdminOptions.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is using a rich text editor / getting maintainer"
        )
        AdminControl = self.go(1)
        ser = AdminOptionsMaintainerSerializer(AdminControl)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class AdminControlsDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AdminOptions.objects.get(pk=pk)
        except AdminOptions.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        AdminControl = self.go(pk)
        ser = AdminOptionsSerializer(AdminControl)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        AdminControl = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting admincontrols {AdminControl}")
        AdminControl.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        AdminControl = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating {AdminControl}")

        # Get the current guide_content
        current_guide_content = AdminControl.guide_content or {}

        # If guide_content is being updated, merge with existing content
        if "guide_content" in req.data:
            # Merge existing content with new content
            updated_guide_content = {
                **current_guide_content,
                **req.data["guide_content"],
            }
            req.data["guide_content"] = updated_guide_content

        ser = AdminOptionsSerializer(
            AdminControl,
            data=req.data,
            partial=True,
        )

        if ser.is_valid():
            updated_admin_options = ser.save()
            print(req.data)
            print(updated_admin_options)
            return Response(
                AdminOptionsSerializer(updated_admin_options).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AdminControlsGuideContentUpdate(APIView):
    """Separate view for updating guide content"""

    permission_classes = [IsAdminUser]

    def go(self, pk):
        try:
            obj = AdminOptions.objects.get(pk=pk)
        except AdminOptions.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        """Update a specific guide content field"""
        AdminControl = self.go(pk)
        field_key = req.data.get("field_key")
        content = req.data.get("content")

        print(f"Received update request for field_key: {field_key}")
        print(f"Content length: {len(content) if content else 'None'}")

        if field_key and content is not None:
            # Initialise guide_content if it doesn't exist or is None
            if (
                not hasattr(AdminControl, "guide_content")
                or AdminControl.guide_content is None
            ):
                AdminControl.guide_content = {}

            # Make sure guide_content is a dict
            if not isinstance(AdminControl.guide_content, dict):
                AdminControl.guide_content = {}

            # Update the specific field
            AdminControl.guide_content[field_key] = content

            # Save with the full object, not just the field
            AdminControl.save()

            # Double-check the save worked
            refreshed = AdminOptions.objects.get(pk=AdminControl.pk)
            saved_content = (
                refreshed.guide_content.get(field_key)
                if refreshed.guide_content
                else None
            )
            print(
                f"Saved content length for {field_key}: {len(saved_content) if saved_content else 'None'}"
            )

            settings.LOGGER.info(
                msg=f"{req.user} updated guide content field {field_key}"
            )
            return Response({"status": "content updated"}, status=HTTP_200_OK)

        print(
            f"Missing data: field_key={field_key}, content={'Present' if content else 'Missing'}"
        )
        return Response(
            {"error": "field_key and content are required"}, status=HTTP_400_BAD_REQUEST
        )


# Add new viewsets for GuideSection and ContentField
class GuideSectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing guide sections"""

    queryset = GuideSection.objects.all().order_by("order")
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GuideSectionCreateUpdateSerializer
        return GuideSectionSerializer

    def perform_create(self, serializer):
        section = serializer.save()
        settings.LOGGER.info(
            msg=f"{self.request.user} created guide section {section.id}"
        )

    def perform_update(self, serializer):
        section = serializer.save()
        settings.LOGGER.info(
            msg=f"{self.request.user} updated guide section {section.id}"
        )

    def perform_destroy(self, instance):
        settings.LOGGER.info(
            msg=f"{self.request.user} deleted guide section {instance.id}"
        )
        instance.delete()

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """Endpoint to reorder sections"""
        section_ids = request.data.get("section_ids", [])

        for index, section_id in enumerate(section_ids):
            try:
                section = GuideSection.objects.get(id=section_id)
                section.order = index
                section.save(update_fields=["order"])
            except GuideSection.DoesNotExist:
                pass

        settings.LOGGER.info(msg=f"{request.user} reordered guide sections")
        return Response({"status": "sections reordered"}, status=HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reorder_fields(self, request, pk=None):
        """Endpoint to reorder content fields within a section"""
        field_ids = request.data.get("field_ids", [])

        for index, field_id in enumerate(field_ids):
            try:
                field = ContentField.objects.get(id=field_id, section_id=pk)
                field.order = index
                field.save(update_fields=["order"])
            except ContentField.DoesNotExist:
                pass

        settings.LOGGER.info(
            msg=f"{request.user} reordered content fields in section {pk}"
        )
        return Response({"status": "content fields reordered"}, status=HTTP_200_OK)


class ContentFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for managing content fields within guide sections"""

    queryset = ContentField.objects.all()
    serializer_class = ContentFieldSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        field = serializer.save()
        settings.LOGGER.info(
            msg=f"{self.request.user} created content field {field.id}"
        )

    def perform_update(self, serializer):
        field = serializer.save()
        settings.LOGGER.info(
            msg=f"{self.request.user} updated content field {field.id}"
        )

    def perform_destroy(self, instance):
        settings.LOGGER.info(
            msg=f"{self.request.user} deleted content field {instance.id}"
        )
        instance.delete()


class AdminTasks(APIView):
    permission_classes = [IsAuthenticated]

    def check_existing_deletion_task(self, data):
        if AdminTask.objects.filter(
            action=data["action"],
            project=data["project"],
            status=AdminTask.TaskStatus.PENDING,
        ).exists():
            return True
        return False

    def check_existing_merge_user_task(self, data):
        if AdminTask.objects.filter(
            action=data["action"],
            primary_user=data["primary_user"],
            secondary_users=data["secondary_users"],
            status=AdminTask.TaskStatus.PENDING,
        ).exists():
            return True
        return False

    def check_existing_caretaker_task(self, data):
        if AdminTask.objects.filter(
            action=data["action"],
            primary_user=data["primary_user"],
            # secondary_users=data["secondary_users"],
            status=AdminTask.TaskStatus.PENDING,
        ).exists():
            return True
        return False

    def check_existing_caretaker_object(self, data):
        if Caretaker.objects.filter(
            user=data["primary_user"],
            caretaker=data["secondary_users"][0],
        ).exists():
            return True
        return False

    def set_project_deletion_requested(self, data):
        try:
            project = Project.objects.get(pk=data["project"])
            # Prevent duplicate requests
            if project.deletion_requested:
                return "Project already has a deletion request"

            project.deletion_requested = True
            project.save()
            return True
        except Exception as e:
            settings.LOGGER.error(
                msg=f"Error in setting project deletion requested: {e}"
            )
            return e

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting all admin tasks")
        all = AdminTask.objects.all()
        ser = AdminTaskSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        details_string = ""
        data = req.data
        if req.data["action"] == AdminTask.ActionTypes.MERGEUSER:
            details_string = f"{req.user} wishes to merge {req.data['secondary_users']} into {req.data['primary_user']}"
        elif req.data["action"] == AdminTask.ActionTypes.SETCARETAKER:
            details_string = f"{req.user} wishes to set {req.data['secondary_users'][0]} as caretaker for {req.data['primary_user']}"
        else:
            details_string = (
                f"{req.user} wishes to delete project {req.data['project']}"
            )

        settings.LOGGER.info(
            msg=f"{req.user} is posting an instance of admin tasks ({req.data['action']} - {details_string})"
        )
        try:
            # Caretaker/Merge user request validation
            if (
                data["action"] == AdminTask.ActionTypes.MERGEUSER
                or data["action"] == AdminTask.ActionTypes.SETCARETAKER
            ) and (
                data["primary_user"] is None
                or data["secondary_users"] is None
                or len(data["secondary_users"]) < 1
            ):
                raise ValueError(
                    "Primary and single secondary users must be set to merge"
                )

            # Delete project request validation
            if (data["action"] == AdminTask.ActionTypes.DELETEPROJECT) and (
                data["project"] is None
            ):
                raise ValueError("Project must be set to delete")
            if data["action"] == AdminTask.ActionTypes.DELETEPROJECT:
                if data["reason"] is None:
                    raise ValueError("Reason must be set to delete project")

        except Exception as e:
            settings.LOGGER.error(msg=f"Error in creating task: {e}")
            return Response(
                e,
                status=HTTP_400_BAD_REQUEST,
            )

        requester = req.user
        data["requester"] = requester.pk
        data["status"] = AdminTask.TaskStatus.PENDING

        if data["action"] == AdminTask.ActionTypes.DELETEPROJECT:
            # First check if there is already a pending deletion request for this project
            if self.check_existing_deletion_task(data):
                settings.LOGGER.error(
                    msg=f"Error in setting project deletion requested: Project already has a pending deletion request"
                )
                return Response(
                    "Project already has a pending deletion request",
                    status=HTTP_400_BAD_REQUEST,
                )
            # Check the project specifically if the flag is set to true
            res = self.set_project_deletion_requested(data)
            if res != True:
                settings.LOGGER.error(
                    msg=f"Error in setting project deletion requested: {res}"
                )
                return Response(
                    f"{res}",
                    status=HTTP_400_BAD_REQUEST,
                )
        elif data["action"] == AdminTask.ActionTypes.MERGEUSER:
            # First check if there is already a pending merge user request for these users
            if self.check_existing_merge_user_task(data):
                settings.LOGGER.error(
                    msg=f"Error in setting merge user requested: Users already have a pending merge user request"
                )
                return Response(
                    "Users already have a pending merge user request",
                    status=HTTP_400_BAD_REQUEST,
                )

        elif data["action"] == AdminTask.ActionTypes.SETCARETAKER:
            # Validate end_date is not in the past
            if data.get("end_date"):
                from django.utils import timezone
                from datetime import datetime
                
                # Parse the end_date
                try:
                    if isinstance(data["end_date"], str):
                        end_date = datetime.fromisoformat(data["end_date"].replace('Z', '+00:00')).date()
                    else:
                        end_date = data["end_date"]
                    
                    if end_date < timezone.now().date():
                        settings.LOGGER.error(
                            msg=f"Error in setting caretaker: End date cannot be in the past"
                        )
                        return Response(
                            "End date cannot be in the past",
                            status=HTTP_400_BAD_REQUEST,
                        )
                except (ValueError, AttributeError) as e:
                    settings.LOGGER.error(
                        msg=f"Error parsing end_date: {e}"
                    )
                    return Response(
                        "Invalid end date format",
                        status=HTTP_400_BAD_REQUEST,
                    )
            
            # First check if there is already a pending caretaker request for this user
            if self.check_existing_caretaker_task(data):
                settings.LOGGER.error(
                    msg=f"Error in setting caretaker: User already has a pending caretaker request"
                )
                return Response(
                    "User already has a pending caretaker request",
                    status=HTTP_400_BAD_REQUEST,
                )
            if self.check_existing_caretaker_object(data):
                settings.LOGGER.error(
                    msg=f"Error in setting caretaker: User already has a caretaker"
                )
                return Response(
                    "User already has a caretaker",
                    status=HTTP_400_BAD_REQUEST,
                )

        # If all is good, and not admin create the task

        # if not req.user.is_superuser:
        ser = AdminTaskRequestCreationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            task = ser.save()
            return Response(
                AdminTaskRequestCreationSerializer(task).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )
        # else:
        #     # Create and fulfill the task


class PendingTasks(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting all pending admin tasks")
        
        # Auto-cancel expired pending caretaker requests before returning
        from django.utils import timezone
        
        expired_caretaker_requests = AdminTask.objects.filter(
            status=AdminTask.TaskStatus.PENDING,
            action=AdminTask.ActionTypes.SETCARETAKER,
            end_date__lt=timezone.now().date()
        )
        
        if expired_caretaker_requests.exists():
            count = expired_caretaker_requests.count()
            settings.LOGGER.info(
                msg=f"Auto-cancelling {count} expired caretaker request(s)"
            )
            for request in expired_caretaker_requests:
                request.status = AdminTask.TaskStatus.CANCELLED
                request.notes = (request.notes or "") + "\n[Auto-cancelled: end date passed while request was pending]"
                request.save()
        
        # Get all remaining pending tasks
        all = AdminTask.objects.filter(status=AdminTask.TaskStatus.PENDING)
        ser = AdminTaskSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class CheckPendingCaretakerRequestForUser(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"{req.user} is checking if user with pk {pk} has an open caretaker request"
        )
        has_request = AdminTask.objects.filter(
            primary_user=pk,
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        ).exists()
        return Response(
            {"has_request": has_request},
            status=HTTP_200_OK,
        )


class GetPendingCaretakerRequestsForUser(APIView):
    """
    Get all pending caretaker requests for a specific user
    Returns requests where someone wants to become THIS user's caretaker
    """
    permission_classes = [IsAuthenticated]

    def get(self, req):
        user_id = req.query_params.get('user_id')
        
        if not user_id:
            return Response(
                {"error": "user_id query parameter is required"},
                status=HTTP_400_BAD_REQUEST,
            )
        
        settings.LOGGER.info(
            msg=f"{req.user} is getting pending caretaker requests for user {user_id}"
        )
        
        # Get all pending caretaker requests for this user
        pending_requests = AdminTask.objects.filter(
            primary_user=user_id,
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        )
        
        # Serialize the requests
        serializer = AdminTaskSerializer(pending_requests, many=True)
        
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


class PendingCaretakerTasks(APIView):
    permission_classes = [IsAuthenticated]

    def get_directorate_documents(self, project_queryset):
        """
        Returns documents requiring Directorate attention
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=False,
        )

    def get_ba_documents(self, project_queryset):
        """
        Returns documents requiring BA attention
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
        )

    def get_lead_documents(self, project_queryset):
        """
        Returns documents requiring project lead attention
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            project_lead_approval_granted=False,
        )

    def get_all_caretaker_assignments(self, user_id, processed_users=None):
        """
        Recursively gather all caretaker assignments, including nested relationships.

        Args:
            user_id: The ID of the user to get assignments for
            processed_users: Set of user IDs already processed (to prevent infinite loops)

        Returns:
            List of all Caretaker assignments, including nested relationships
        """
        if processed_users is None:
            processed_users = set()

        # If we've already processed this user, return empty list to prevent cycles
        if user_id in processed_users:
            return []

        # Add current user to processed set
        processed_users.add(user_id)

        # Get direct caretaker assignments for this user
        direct_assignments = Caretaker.objects.filter(caretaker=user_id)
        all_assignments = list(direct_assignments)

        # For each user being caretaken, get their caretaker assignments
        for assignment in direct_assignments:
            nested_assignments = self.get_all_caretaker_assignments(
                assignment.user.id, processed_users
            )
            all_assignments.extend(nested_assignments)

        return all_assignments

    def return_deduplicated_docs(self, docs, is_serialized=False):
        """
        Returns a list of unique document tasks, removing duplicates based on document pk and document kind.

        Args:
            docs: List of documents (either serialized data or model instances)
            is_serialized: Boolean indicating if the docs are already serialized (default: False)

        Returns:
            List of unique documents
        """
        doc_dict = {}

        for doc in docs:
            try:
                if is_serialized:
                    # For serialized data, doc is a dictionary
                    key = f"{doc["pk"]}_{doc["kind"]}"

                else:
                    # For model instances, doc is a ProjectDocument object
                    key = f"{doc.pk}_{getattr(doc, 'kind', '')}"

                # print("Key is ", key)
                if key in doc_dict:
                    # Skip duplicates
                    continue
                    # doc_dict[key] = doc

                doc_dict[key] = doc

            except (KeyError, AttributeError) as e:
                # Log error but continue processing
                print(f"Error processing document: {e}")
                continue

        # print(
        #     {
        #         "Before:": len(docs),
        #         "After:": len(doc_dict),
        #     }
        # )

        return list(doc_dict.values())

    def get(self, request, pk):
        settings.LOGGER.info(
            msg=f"{request.user} is getting pending caretaker documents pending action"
        )

        # 1) Gather caretaker assignments
        # caretaker_assignments = Caretaker.objects.filter(caretaker=pk)
        # the actual "users" being cared for
        # caretaker_users = [assignment.user for assignment in caretaker_assignments]

        caretaker_assignments = self.get_all_caretaker_assignments(pk)

        # 2) Determine if at least one caretaker user is "Directorate" or superuser
        #    Similarly, gather all BA leader user IDs, etc.
        directorate_user_found = False
        ba_leader_user_ids = set()
        project_lead_user_ids = set()
        team_member_user_ids = set()

        for assignment in caretaker_assignments:
            user = assignment.user
            user_ba = user.work.business_area if hasattr(user, "work") else None

            # Check Directorate
            if (
                not request.user.is_superuser
                and (user_ba and user_ba.name == "Directorate")
                or user.is_superuser
            ):
                directorate_user_found = True

            # Check if BA leader
            business_areas_led = user.business_areas_led.values_list("id", flat=True)
            if business_areas_led:
                ba_leader_user_ids.add(user.id)

            # Check if project lead
            # This will help gather project lead IDs for further filtering
            lead_memberships = ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(user=user, is_leader=True)
            if lead_memberships.exists():
                project_lead_user_ids.add(user.id)

            # Check if team member (non-leader)
            non_leader_memberships = ProjectMember.objects.filter(
                user=user, is_leader=False
            )
            if non_leader_memberships.exists():
                team_member_user_ids.add(user.id)

        # 3) Find the relevant projects
        active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY)

        # 4) Build up the final document list from each condition
        all_documents = []

        # 4a) Directorate docs
        directorate_documents = []
        if directorate_user_found:
            directorate_documents = self.get_directorate_documents(active_projects)
            all_documents.extend(directorate_documents)

        # 4b) BA docs
        ba_documents = []
        if ba_leader_user_ids:
            # Find all BA-led projects for those user(s)
            # Possibly you need more advanced logic if BA is the business_area of the project, etc.
            ba_projects = active_projects.filter(
                business_area__leader__in=ba_leader_user_ids
            )
            ba_documents = self.get_ba_documents(ba_projects)
            all_documents.extend(ba_documents)

        # 4c) Project lead docs
        lead_documents = []
        if project_lead_user_ids:
            # Projects led by those caretaker users
            lead_projects = ProjectMember.objects.filter(
                user_id__in=project_lead_user_ids, is_leader=True
            ).values_list("project_id", flat=True)
            lead_documents = self.get_lead_documents(lead_projects)
            all_documents.extend(lead_documents)

        # 4d) Team member docs
        # If you need separate logic for normal team members, do so similarly
        member_documents = []
        if team_member_user_ids:
            # This example reuses the same lead_documents filter with
            # project_lead_approval_granted=False, but specifically for those team members’ projects
            # You might need a separate query if your logic differs.
            team_projects = ProjectMember.objects.filter(
                user_id__in=team_member_user_ids,
                is_leader=False,
                project__in=active_projects,
            ).values_list("project_id", flat=True)

            member_documents = ProjectDocument.objects.exclude(
                status=ProjectDocument.StatusChoices.APPROVED
            ).filter(
                project__in=team_projects,
                project_lead_approval_granted=False,
            )
            all_documents.extend(member_documents)

        # Directorate documents - use None for for_user
        ser_directorate = TinyProjectDocumentSerializerWithUserDocsBelongTo(
            directorate_documents,
            many=True,
            context={"request": request, "for_user": None},
        )

        # BA documents - serialize for each BA leader
        ba_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.business_areas_led.exists():
                # Filter BA documents for just this user's business areas
                user_ba_areas = assignment.user.business_areas_led.values_list(
                    "id", flat=True
                )
                user_ba_documents = ba_documents.filter(
                    project__business_area__in=user_ba_areas
                )

                ser = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_ba_documents,  # Now only passing this user's BA documents
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                ba_serialized.extend(ser.data)

        # Lead documents - serialize for each project lead
        lead_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in project_lead_user_ids:
                # Filter lead_documents for just this user's projects
                user_lead_projects = ProjectMember.objects.filter(
                    user=assignment.user, is_leader=True
                ).values_list("project_id", flat=True)

                user_lead_documents = lead_documents.filter(
                    project__in=user_lead_projects
                )

                ser = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_lead_documents,  # Now only passing this user's documents
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                lead_serialized.extend(ser.data)

        # Team member documents - serialize for each team member
        member_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in team_member_user_ids:
                # Filter member documents for just this user's projects
                user_team_projects = ProjectMember.objects.filter(
                    user=assignment.user, is_leader=False, project__in=active_projects
                ).values_list("project_id", flat=True)

                user_member_documents = member_documents.filter(
                    project__in=user_team_projects
                )

                ser = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_member_documents,  # Now only passing this user's team documents
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                member_serialized.extend(ser.data)

        # All documents - combine all serialized data and REMOVE DUPLICATES FROM EACH LIST
        all_serialized = []
        if directorate_documents:
            all_serialized.extend(ser_directorate.data)
        all_serialized.extend(ba_serialized)
        all_serialized.extend(lead_serialized)
        all_serialized.extend(member_serialized)

        data = {
            "all": self.return_deduplicated_docs(all_serialized, is_serialized=True),
            "directorate": self.return_deduplicated_docs(
                ser_directorate.data, is_serialized=True
            ),
            "ba": self.return_deduplicated_docs(ba_serialized, is_serialized=True),
            "lead": self.return_deduplicated_docs(lead_serialized, is_serialized=True),
            "team": self.return_deduplicated_docs(
                member_serialized, is_serialized=True
            ),
        }

        return Response(data, status=HTTP_200_OK)


class AdminTaskDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AdminTask.objects.get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        admin_task = self.go(pk)
        ser = AdminTaskSerializer(admin_task)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        admin_task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting admin_task {admin_task}")
        admin_task.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        admin_task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating {admin_task}")
        ser = AdminTaskSerializer(
            admin_task,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_admin_task = ser.save()
            return Response(
                AdminTaskSerializer(updated_admin_task).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================

# region Caretaker =================================================================================================


class Caretakers(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting all caretakers")
        all = Caretaker.objects.all()
        ser = CaretakerSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is posting/approving an instance of caretaker"
        )
        ser = CaretakerSerializer(
            data=req.data,
        )
        if ser.is_valid():
            caretaker = ser.save()
            return Response(
                CaretakerSerializer(caretaker).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class CaretakerDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Caretaker.objects.get(pk=pk)
        except Caretaker.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        caretaker = self.go(pk)
        ser = CaretakerSerializer(caretaker)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        caretaker = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting caretaker {caretaker}")
        caretaker.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        caretaker = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating {caretaker}")
        ser = CaretakerSerializer(
            caretaker,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_caretaker = ser.save()
            return Response(
                CaretakerSerializer(updated_caretaker).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class CheckCaretaker(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is checking if they have a caretaker")
        user = req.user
        
        # Get caretaker object
        caretaker_object = Caretaker.objects.filter(user=user)
        if caretaker_object.exists():
            caretaker_object = caretaker_object.first()
        else:
            caretaker_object = None
        
        # Get pending caretaker requests
        caretaker_request_object = AdminTask.objects.filter(
            primary_user=user,
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        )
        become_caretaker_request_object = AdminTask.objects.filter(
            # Check if user in secondary users
            secondary_users__contains=[user.pk],
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        )
        
        # Auto-cancel expired pending requests
        from django.utils import timezone
        
        if caretaker_request_object.exists():
            request = caretaker_request_object.first()
            # Check if request has an end_date that has passed
            if request.end_date and request.end_date.date() < timezone.now().date():
                settings.LOGGER.info(
                    msg=f"Auto-cancelling expired caretaker request {request.id} for user {user.pk}"
                )
                request.status = AdminTask.TaskStatus.CANCELLED
                request.notes = (request.notes or "") + "\n[Auto-cancelled: end date passed while request was pending]"
                request.save()
                caretaker_request_object = None
            else:
                caretaker_request_object = request
        else:
            caretaker_request_object = None
            
        if become_caretaker_request_object.exists():
            request = become_caretaker_request_object.first()
            # Check if request has an end_date that has passed
            if request.end_date and request.end_date.date() < timezone.now().date():
                settings.LOGGER.info(
                    msg=f"Auto-cancelling expired become caretaker request {request.id} for user {user.pk}"
                )
                request.status = AdminTask.TaskStatus.CANCELLED
                request.notes = (request.notes or "") + "\n[Auto-cancelled: end date passed while request was pending]"
                request.save()
                become_caretaker_request_object = None
            else:
                become_caretaker_request_object = request
        else:
            become_caretaker_request_object = None
            
        return Response(
            {
                "caretaker_object": (
                    CaretakerSerializer(caretaker_object).data
                    if caretaker_object
                    else None
                ),
                "caretaker_request_object": (
                    AdminTaskSerializer(caretaker_request_object).data
                    if caretaker_request_object
                    else None
                ),
                "become_caretaker_request_object": (
                    AdminTaskSerializer(become_caretaker_request_object).data
                    if become_caretaker_request_object
                    else None
                ),
            },
            status=HTTP_200_OK,
        )


# endregion  =================================================================================================

# region Functions on approval of tasks =================================================================================================


class ApproveTask(APIView):
    permission_classes = [IsAdminUser]

    def go(self, pk):
        try:
            obj = AdminTask.objects.get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound
        return obj

    def get_user(self, pk):
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound
        return obj

    def get_memberships(self, user):
        try:
            obj = ProjectMember.objects.filter(user=user)
        except ProjectMember.DoesNotExist:
            raise NotFound
        return obj

    def get_projects(self, user):
        try:
            obj = Project.objects.filter(members__user=user)
        except Project.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is approving task {task}")

        # Approve the task
        task.status = AdminTask.TaskStatus.APPROVED
        task.save()

        # Run related functionality
        with transaction.atomic():
            try:
                if task.action == AdminTask.ActionTypes.DELETEPROJECT:
                    if task.project is None:
                        raise ValueError("Project must be set to delete")
                    task.notes = f"Project deletion approved - {task.project.title}"
                    task.project.delete()
                    task.project = None
                    # This will delete all related documents and memberships
                elif task.action == AdminTask.ActionTypes.MERGEUSER:
                    if (
                        task.primary_user is None
                        or task.secondary_users is None
                        or len(task.secondary_users) < 1
                    ):
                        raise ValueError(
                            "Primary and single secondary users must be set to merge"
                        )
                    # Get the primary user
                    user_to_merge_into = self.get_user(task.primary_user.pk)
                    # Get the secondary user/s
                    users_to_merge = [self.get_user(u) for u in task.secondary_users]
                    primary_is_staff = user_to_merge_into.is_staff
                    for merging_user in users_to_merge:
                        # ========= HANDLE THE PROJECT MEMBERSHIPS =========
                        # Merge the users projects and memberships into the primary user
                        for membership in self.get_memberships(merging_user):
                            # First check if a membership already exists for the primary user
                            existing_membership = ProjectMember.objects.filter(
                                project=membership.project, user=user_to_merge_into
                            ).exists()
                            if existing_membership:
                                # If it does and they are leader, retain the leader status
                                if (
                                    membership.role
                                    == ProjectMember.RoleChoices.SUPERVISING
                                    or existing_membership.role
                                    == ProjectMember.RoleChoices.SUPERVISING
                                ):
                                    existing_membership.role = (
                                        ProjectMember.RoleChoices.SUPERVISING
                                    )
                                else:
                                    if primary_is_staff:
                                        if membership.role in [
                                            ProjectMember.RoleChoices.RESEARCH,
                                            ProjectMember.RoleChoices.TECHNICAL,
                                        ]:
                                            existing_membership.role = membership.role
                                    else:
                                        if membership.role in [
                                            ProjectMember.RoleChoices.EXTERNALCOL,
                                            ProjectMember.RoleChoices.EXTERNALPEER,
                                            ProjectMember.RoleChoices.ACADEMICSUPER,
                                            ProjectMember.RoleChoices.STUDENT,
                                            ProjectMember.RoleChoices.CONSULTED,
                                            ProjectMember.RoleChoices.GROUP,
                                        ]:
                                            existing_membership.role = membership.role
                                # Save the existing membership
                                existing_membership.save()
                                # Remove the old membership
                                membership.delete()
                            # If no existing membership with the same user, change the secondary users membership to the primary user
                            else:
                                membership.user = user_to_merge_into
                                # Ensure that the role is appropriate for the primary user
                                if primary_is_staff:
                                    if membership.role in [
                                        ProjectMember.RoleChoices.RESEARCH,
                                        ProjectMember.RoleChoices.TECHNICAL,
                                    ]:
                                        membership.role = membership.role
                                else:
                                    if membership.role in [
                                        ProjectMember.RoleChoices.EXTERNALCOL,
                                        ProjectMember.RoleChoices.EXTERNALPEER,
                                        ProjectMember.RoleChoices.ACADEMICSUPER,
                                        ProjectMember.RoleChoices.STUDENT,
                                        ProjectMember.RoleChoices.CONSULTED,
                                        ProjectMember.RoleChoices.GROUP,
                                    ]:
                                        membership.role = membership.role
                                membership.save()

                        # ========= HANDLE DELETION =========
                        # Delete the user
                        merging_user.delete()

                elif task.action == AdminTask.ActionTypes.SETCARETAKER:
                    # Set the caretaker
                    # Get the primary user
                    user_who_needs_caretaker = self.get_user(task.primary_user.pk)
                    # Get the caretaker
                    caretaker = self.get_user(task.secondary_users[0])
                    # Create the caretaker
                    Caretaker.objects.create(
                        user=user_who_needs_caretaker,
                        caretaker=caretaker,
                        reason=task.reason,
                        end_date=task.end_date,  # This will be null if the caretaker is permanent
                        notes=task.notes,
                    )
                else:
                    raise ValueError("Task action not recognised")

            except Exception as e:
                settings.LOGGER.error(msg=f"Error in fulfilling task: {e}")
                return Response(
                    status=HTTP_400_BAD_REQUEST,
                )

            # Fulfill the task
            task.status = AdminTask.TaskStatus.FULFILLED
            task.save()

            return Response(
                status=HTTP_202_ACCEPTED,
            )


class RejectTask(APIView):

    permission_classes = [IsAdminUser]

    def go(self, pk):
        try:
            obj = AdminTask.objects.get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound
        return obj

    def get_user(self, pk):
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is rejecting task {task}")

        # Reject the task
        task.status = AdminTask.TaskStatus.REJECTED
        task.save()

        # Handle based on type of task
        if task.action == AdminTask.ActionTypes.DELETEPROJECT:
            # If a project deletion is rejected, the project deletion is cancelled
            task.project.deletion_requested = False
            task.project.save()
            # Potentially extend to send emails of rejection

        if task.action == AdminTask.ActionTypes.SETCARETAKER:
            # If a caretaker request is rejected, the caretaker request is cancelled, no additional action is required
            # Potentially extend to send emails of rejection
            pass

        if task.action == AdminTask.ActionTypes.MERGEUSER:
            # If a user merge is rejected, the merge is cancelled
            # Potentially extend to send emails of rejection
            pass

        return Response(
            status=HTTP_202_ACCEPTED,
        )


class CancelTask(APIView):

    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AdminTask.objects.get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound
        return obj

    def get_user(self, pk):
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is cancelling request for task {task}")

        # Cancel the task
        task.status = AdminTask.TaskStatus.CANCELLED
        task.save()

        # Handle based on type of task
        if task.action == AdminTask.ActionTypes.DELETEPROJECT:
            # If a project deletion is cancelled, the project deletion is cancelled
            task.project.deletion_requested = False
            task.project.save()

        if task.action == AdminTask.ActionTypes.MERGEUSER:
            # If a user merge is cancelled, the merge is cancelled
            pass

        if task.action == AdminTask.ActionTypes.SETCARETAKER:
            # If a caretaker request is cancelled, the caretaker request is cancelled
            # Note: task.primary_user is a User object, not a pk
            if task.primary_user:
                primary_user = task.primary_user
                primary_user.caretaker_mode = False
                primary_user.save()

        return Response(
            status=HTTP_202_ACCEPTED,
        )


# endregion  =================================================================================================

# region Merge Users / Set Caretaker =================================================================================================


class MergeUsers(APIView):
    """
    Merges a list of users into a primary user.
    For each user in the list, the project members, comments, documents are updated to the primary user.
    The primary user's data is not overwritten, higher privelleges take priority, and the secondary users are deleted.
    """

    permission_classes = [IsAdminUser]

    def get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is merging users")
        if not req.user.is_superuser:
            return Response(
                {"detail": "You do not have permission to merge users."},
                status=HTTP_401_UNAUTHORIZED,
            )

        primary_user_id = req.data.get("primaryUser")
        secondary_user_ids = req.data.get("secondaryUsers")

        if not primary_user_id or not secondary_user_ids:
            return Response(
                {"detail": "Invalid data. Primary and secondary users are required."},
                status=HTTP_400_BAD_REQUEST,
            )

        if primary_user_id in secondary_user_ids:
            return Response(
                {
                    "detail": "Invalid data. Primary user cannot also be a secondary user."
                },
                status=HTTP_400_BAD_REQUEST,
            )

        primary_user = self.get_user(primary_user_id)
        secondary_users = User.objects.filter(pk__in=secondary_user_ids)
        print({"primaryUser": primary_user, "secondaryUsers": secondary_users})

        with transaction.atomic():

            for u in secondary_users:
                # Inherit the projects of the secondary user
                user_projects = ProjectMember.objects.filter(user=u)
                user_projects.update(user=primary_user)

                # Inherit the roles of the secondary user
                for project in user_projects:
                    # Handle if the primary user is also in the project
                    primary_user_in_project = ProjectMember.objects.filter(
                        project=project.project, user=primary_user
                    ).exists()
                    if primary_user_in_project:
                        # If the primary user is also in the project and they have a higher role, do not overwrite their role, otherwise overwrite
                        primary_users_membership = ProjectMember.objects.get(
                            project=project.project, user=primary_user
                        )

                        # First check if they are leading the project, if so, retain the primary user role
                        if (
                            primary_users_membership.role
                            in [
                                ProjectMember.RoleChoices.SUPERVISING,
                            ]
                            and primary_user.is_staff
                        ):
                            primary_users_membership.role = (
                                primary_users_membership.role
                            )
                        # If not leading, set to the secondary user role
                        elif (
                            project.role
                            in [
                                ProjectMember.RoleChoices.SUPERVISING,
                                ProjectMember.RoleChoices.RESEARCH,
                                ProjectMember.RoleChoices.TECHNICAL,
                            ]
                            and primary_user.is_staff
                        ):
                            primary_users_membership.role = project.role

                    # Handle if the primary user is not in the project
                    else:
                        # If staff, must have staff role
                        if primary_user.is_staff:
                            if project.role in [
                                ProjectMember.RoleChoices.SUPERVISING,
                                ProjectMember.RoleChoices.RESEARCH,
                                ProjectMember.RoleChoices.TECHNICAL,
                            ]:
                                project.role = project.role
                            else:
                                project.role = ProjectMember.RoleChoices.RESEARCH
                        # If not staff, cannot have staff roles
                        else:
                            if project.role in [
                                ProjectMember.RoleChoices.EXTERNALCOL,
                                ProjectMember.RoleChoices.EXTERNALPEER,
                                ProjectMember.RoleChoices.ACADEMICSUPER,
                                ProjectMember.RoleChoices.STUDENT,
                                ProjectMember.RoleChoices.CONSULTED,
                                ProjectMember.RoleChoices.GROUP,
                            ]:
                                project.role = project.role
                            else:
                                project.role = ProjectMember.RoleChoices.EXTERNALCOL
                    project.save()

                # Inherit the documents of the secondary user
                user_created_documents = ProjectDocument.objects.filter(creator=u)
                user_created_documents.update(creator=primary_user)
                user_modified_documents = ProjectDocument.objects.filter(modifier=u)
                user_modified_documents.update(modifier=primary_user)

                # Inherit the comments of the secondary user
                user_comments = Comment.objects.filter(user=u)
                user_comments.update(user=primary_user)

                # Delete the user (associated fields will cascade delete on deletion of the user)
                u.delete()

        return Response(status=HTTP_200_OK)


class AdminSetCaretaker(APIView):
    permission_classes = [IsAdminUser]

    def get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is setting a caretaker")
        if not req.user.is_superuser:
            return Response(
                {"detail": "You do not have permission to set a caretaker."},
                status=HTTP_401_UNAUTHORIZED,
            )

        primary_user_id = req.data.get("userPk")
        secondary_user_id = req.data.get("caretakerPk")
        reason = req.data.get("reason")
        end_date = req.data.get("endDate")
        notes = req.data.get("notes")

        if not primary_user_id or not secondary_user_id:
            return Response(
                {"detail": "Invalid data. Primary and secondary users are required."},
                status=HTTP_400_BAD_REQUEST,
            )

        if primary_user_id == secondary_user_id:
            return Response(
                {"detail": "Invalid data. Primary user cannot also be secondary user."},
                status=HTTP_400_BAD_REQUEST,
            )

        if not reason:
            return Response(
                {"detail": "Invalid data. Reason is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        primary_user = self.get_user(primary_user_id)
        secondary_user = self.get_user(secondary_user_id)
        # Reject if secondary user has a caretaker
        if secondary_user.caretaker.exists():
            return Response(
                {"detail": "Cannot set a user with a caretaker as caretaker."},
                status=HTTP_400_BAD_REQUEST,
            )

        print({"primaryUser": primary_user, "secondaryUsers": secondary_user})

        with transaction.atomic():
            Caretaker.objects.create(
                user=primary_user,
                caretaker=secondary_user,
                reason=reason,
                end_date=end_date if end_date else None,
                notes=notes if notes else None,
            )

        return Response(status=HTTP_200_OK)


class SetCaretaker(APIView):
    """
    Sets a caretaker for a user.
    The caretaker is a user who can act on behalf of the user.
    """

    permission_classes = [IsAdminUser]

    def get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is setting a caretaker")
        if not req.user.is_superuser:
            return Response(
                {"detail": "You do not have permission to set a caretaker."},
                status=HTTP_401_UNAUTHORIZED,
            )

        primary_user_id = req.data.get("primaryUser")
        secondary_user_ids = req.data.get("secondaryUsers")
        reason = req.data.get("reason")
        end_date = req.data.get("endDate")
        notes = req.data.get("notes")

        if not primary_user_id or not secondary_user_ids:
            return Response(
                {"detail": "Invalid data. Primary and secondary users are required."},
                status=HTTP_400_BAD_REQUEST,
            )

        if primary_user_id in secondary_user_ids:
            return Response(
                {
                    "detail": "Invalid data. Primary user cannot also be a secondary user."
                },
                status=HTTP_400_BAD_REQUEST,
            )

        if not reason:
            return Response(
                {"detail": "Invalid data. Reason is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        primary_user = self.get_user(primary_user_id)
        secondary_users = User.objects.filter(pk__in=secondary_user_ids)
        print({"primaryUser": primary_user, "secondaryUsers": secondary_users})

        with transaction.atomic():
            for caretaker_user in secondary_users:
                Caretaker.objects.create(
                    user=primary_user,
                    caretaker=caretaker_user,
                    reason=reason,
                    end_date=end_date if end_date else None,
                    notes=notes if notes else None,
                )

        return Response(status=HTTP_200_OK)


class RespondToCaretakerRequest(APIView):
    """
    Allow a user to approve or reject a caretaker request where they are the requested caretaker.
    This reduces admin burden by allowing users to self-manage caretaker requests.
    """
    permission_classes = [IsAuthenticated]

    def get_task(self, pk):
        try:
            obj = AdminTask.objects.get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound
        return obj

    def get_user(self, pk):
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        """
        Approve or reject a caretaker request.
        Body: { "action": "approve" | "reject" }
        """
        task = self.get_task(pk)
        action = req.data.get("action")

        # Validate that the task is a caretaker request
        if task.action != AdminTask.ActionTypes.SETCARETAKER:
            return Response(
                {"error": "This endpoint only handles caretaker requests"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Validate that the task is pending
        if task.status != AdminTask.TaskStatus.PENDING:
            return Response(
                {"error": "This request has already been processed"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Validate that the current user is the requested caretaker
        if req.user.pk not in task.secondary_users:
            return Response(
                {"error": "You are not authorized to respond to this request"},
                status=HTTP_401_UNAUTHORIZED,
            )

        # Validate action
        if action not in ["approve", "reject"]:
            return Response(
                {"error": "Action must be 'approve' or 'reject'"},
                status=HTTP_400_BAD_REQUEST,
            )

        settings.LOGGER.info(
            msg=f"{req.user} is {action}ing caretaker request {task}"
        )

        if action == "approve":
            # Approve and fulfill the task
            task.status = AdminTask.TaskStatus.APPROVED
            task.save()

            with transaction.atomic():
                try:
                    # Get the primary user (who needs a caretaker)
                    user_who_needs_caretaker = self.get_user(task.primary_user.pk)
                    # Get the caretaker (current user)
                    caretaker = self.get_user(task.secondary_users[0])

                    # Create the caretaker relationship
                    Caretaker.objects.create(
                        user=user_who_needs_caretaker,
                        caretaker=caretaker,
                        reason=task.reason,
                        end_date=task.end_date,
                        notes=task.notes,
                    )

                    # Fulfill the task
                    task.status = AdminTask.TaskStatus.FULFILLED
                    task.save()

                    return Response(
                        {"message": "Caretaker request approved successfully"},
                        status=HTTP_202_ACCEPTED,
                    )

                except Exception as e:
                    settings.LOGGER.error(msg=f"Error in fulfilling task: {e}")
                    return Response(
                        {"error": "Failed to create caretaker relationship"},
                        status=HTTP_400_BAD_REQUEST,
                    )

        else:  # action == "reject"
            # Reject the task
            task.status = AdminTask.TaskStatus.REJECTED
            task.save()

            return Response(
                {"message": "Caretaker request rejected successfully"},
                status=HTTP_202_ACCEPTED,
            )


# endregion  =================================================================================================
