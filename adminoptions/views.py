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
    ContentField,
    GuideSection,
)
from adminoptions.serializers import (
    AdminOptionsCreateSerializer,
    AdminOptionsMaintainerSerializer,
    AdminOptionsSerializer,
    AdminTaskRequestCreationSerializer,
    AdminTaskSerializer,
    ContentFieldSerializer,
    GuideSectionCreateUpdateSerializer,
    GuideSectionSerializer,
)
from caretakers.models import Caretaker
from caretakers.serializers import CaretakerSerializer
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
        ser = AdminOptionsCreateSerializer(
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

        ser = AdminOptionsCreateSerializer(
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
        # Only return pending tasks (filter out cancelled, rejected, fulfilled)
        pending_tasks = AdminTask.objects.filter(
            status=AdminTask.TaskStatus.PENDING
        )
        ser = AdminTaskSerializer(
            pending_tasks,
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
                {'error': str(e)},
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
            end_date__lt=timezone.now()  # Compare datetime to datetime
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
    Returns requests where someone wants THIS user to become THEIR caretaker
    (i.e., where THIS user is in the secondary_users array)
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
        
        # Get all pending caretaker requests where THIS user is being asked to be the caretaker
        # The user_id should be in the secondary_users array
        pending_requests = AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            secondary_users__contains=[int(user_id)],  # User is in the secondary_users array
        )
        
        # Serialize the requests
        serializer = AdminTaskSerializer(pending_requests, many=True)
        
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


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

                        # ========= HANDLE DOCUMENTS AND COMMENTS =========
                        # Update documents created by merging user
                        user_created_documents = ProjectDocument.objects.filter(creator=merging_user)
                        user_created_documents.update(creator=user_to_merge_into)
                        
                        # Update documents modified by merging user
                        user_modified_documents = ProjectDocument.objects.filter(modifier=merging_user)
                        user_modified_documents.update(modifier=user_to_merge_into)
                        
                        # Update comments by merging user
                        user_comments = Comment.objects.filter(user=merging_user)
                        user_comments.update(user=user_to_merge_into)

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
            pass

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


# NOTE: AdminSetCaretaker and SetCaretaker views removed - duplicates of caretakers app functionality
# Use /api/v1/caretakers/admin-set/ instead


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
