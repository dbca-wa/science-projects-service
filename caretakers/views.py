# region IMPORTS
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound
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

from .models import Caretaker
from .serializers import CaretakerSerializer, CaretakerCreateSerializer
from adminoptions.models import AdminTask
from adminoptions.serializers import AdminTaskSerializer
from users.models import User
from projects.models import Project, ProjectMember
from documents.models import ProjectDocument
from documents.serializers import TinyProjectDocumentSerializerWithUserDocsBelongTo

# endregion


# region Caretaker Relationship Views


class CaretakerList(APIView):
    """List all caretaker relationships or create new one"""
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting all caretakers")
        all_caretakers = Caretaker.objects.all()
        ser = CaretakerSerializer(all_caretakers, many=True)
        return Response(ser.data, status=HTTP_200_OK)

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is posting/approving an instance of caretaker"
        )
        ser = CaretakerCreateSerializer(data=req.data)
        if ser.is_valid():
            caretaker = ser.save()
            return Response(
                CaretakerSerializer(caretaker).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class CaretakerDetail(APIView):
    """Get, update, or delete a caretaker relationship"""
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
        return Response(ser.data, status=HTTP_200_OK)

    def delete(self, req, pk):
        caretaker = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting caretaker {caretaker}")
        caretaker.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def put(self, req, pk):
        caretaker = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating {caretaker}")
        ser = CaretakerSerializer(caretaker, data=req.data, partial=True)
        if ser.is_valid():
            updated_caretaker = ser.save()
            return Response(
                CaretakerSerializer(updated_caretaker).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


# endregion


# region Caretaker Request Views (AdminTask integration)


class CaretakerRequestList(APIView):
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
        pending_requests = AdminTask.objects.filter(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            secondary_users__contains=[int(user_id)],
        )
        
        serializer = AdminTaskSerializer(pending_requests, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ApproveCaretakerRequest(APIView):
    """Approve a caretaker request"""
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
        """Approve a caretaker request"""
        task = self.get_task(pk)

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

        settings.LOGGER.info(
            msg=f"{req.user} is approving caretaker request {task}"
        )

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


class RejectCaretakerRequest(APIView):
    """Reject a caretaker request"""
    permission_classes = [IsAuthenticated]

    def get_task(self, pk):
        try:
            obj = AdminTask.objects.get(pk=pk)
        except AdminTask.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        """Reject a caretaker request"""
        task = self.get_task(pk)

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

        settings.LOGGER.info(
            msg=f"{req.user} is rejecting caretaker request {task}"
        )

        # Reject the task
        task.status = AdminTask.TaskStatus.REJECTED
        task.save()

        return Response(
            {"message": "Caretaker request rejected successfully"},
            status=HTTP_202_ACCEPTED,
        )


# endregion


# region Caretaker Task Views


class CaretakerTasksForUser(APIView):
    """Get tasks for a specific caretakee"""
    permission_classes = [IsAuthenticated]

    def get_directorate_documents(self, project_queryset):
        """Returns documents requiring Directorate attention"""
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    def get_ba_documents(self, project_queryset):
        """Returns documents requiring BA attention"""
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    def get_lead_documents(self, project_queryset):
        """Returns documents requiring project lead attention"""
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            project_lead_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    def get_all_caretaker_assignments(self, user_id, processed_users=None):
        """
        Recursively gather all caretaker assignments, including nested relationships.
        """
        if processed_users is None:
            processed_users = set()

        if user_id in processed_users:
            return []

        processed_users.add(user_id)

        # Get direct caretaker assignments with optimized queries
        direct_assignments = Caretaker.objects.filter(
            caretaker=user_id
        ).select_related(
            'user',
            'user__work',
            'user__work__business_area',
        ).prefetch_related(
            'user__business_areas_led',
        )
        all_assignments = list(direct_assignments)

        # For each user being caretaken, get their caretaker assignments
        for assignment in direct_assignments:
            nested_assignments = self.get_all_caretaker_assignments(
                assignment.user.id, processed_users
            )
            all_assignments.extend(nested_assignments)

        return all_assignments

    def return_deduplicated_docs(self, docs, is_serialized=False):
        """Returns a list of unique document tasks, removing duplicates"""
        doc_dict = {}

        for doc in docs:
            try:
                if is_serialized:
                    key = f"{doc['id']}_{doc['kind']}"
                else:
                    key = f"{doc.pk}_{getattr(doc, 'kind', '')}"

                if key in doc_dict:
                    continue

                doc_dict[key] = doc

            except (KeyError, AttributeError) as e:
                print(f"Error processing document: {e}")
                continue

        return list(doc_dict.values())

    def get(self, request, pk):
        settings.LOGGER.info(
            msg=f"{request.user} is getting pending caretaker documents pending action"
        )

        # Gather caretaker assignments
        caretaker_assignments = self.get_all_caretaker_assignments(pk)

        # Batch query for all project memberships
        caretakee_ids = [assignment.user.id for assignment in caretaker_assignments]
        
        # Single query for all lead memberships
        lead_user_ids = set(
            ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(
                user_id__in=caretakee_ids,
                is_leader=True
            ).values_list('user_id', flat=True)
        )
        
        # Single query for all team memberships
        team_user_ids = set(
            ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(
                user_id__in=caretakee_ids,
                is_leader=False
            ).values_list('user_id', flat=True)
        )
        
        # Determine roles for each caretakee
        directorate_user_found = False
        ba_leader_user_ids = set()
        project_lead_user_ids = lead_user_ids
        team_member_user_ids = team_user_ids

        for assignment in caretaker_assignments:
            user = assignment.user
            user_ba = user.work.business_area if hasattr(user, "work") else None

            # Check Directorate
            if ((user_ba and user_ba.name == "Directorate") or user.is_superuser):
                directorate_user_found = True

            # Check if BA leader
            if user.business_areas_led.exists():
                ba_leader_user_ids.add(user.id)

        # Find the relevant projects
        active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY)

        # Build up the final document list
        all_documents = []

        # Directorate docs
        directorate_documents = []
        if directorate_user_found:
            directorate_documents = self.get_directorate_documents(active_projects)
            
            # Filter out directorate documents that the requesting user already has access to
            requesting_user = request.user
            requesting_user_ba = requesting_user.work.business_area if hasattr(requesting_user, "work") else None
            requesting_user_is_directorate = (
                (requesting_user_ba and requesting_user_ba.name == "Directorate") 
                or requesting_user.is_superuser
            )
            
            if requesting_user_is_directorate:
                directorate_documents = []
            
            all_documents.extend(directorate_documents)

        # BA docs
        ba_documents = []
        if ba_leader_user_ids:
            ba_projects = Project.objects.exclude(
                status=Project.CLOSED_ONLY
            ).filter(
                business_area__leader__in=ba_leader_user_ids
            )
            ba_documents = self.get_ba_documents(ba_projects)
            all_documents.extend(ba_documents)

        # Project lead docs
        lead_documents = []
        if project_lead_user_ids:
            lead_projects = ProjectMember.objects.filter(
                user_id__in=project_lead_user_ids, is_leader=True
            ).values_list("project_id", flat=True)
            lead_documents = self.get_lead_documents(lead_projects)
            all_documents.extend(lead_documents)

        # Team member docs
        member_documents = []
        if team_member_user_ids:
            team_projects = ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(
                user_id__in=team_member_user_ids,
                is_leader=False,
            ).values_list("project_id", flat=True)

            member_documents = ProjectDocument.objects.exclude(
                status=ProjectDocument.StatusChoices.APPROVED
            ).filter(
                project__in=team_projects,
                project_lead_approval_granted=False,
            ).select_related(
                'project',
                'project__business_area',
            )
            all_documents.extend(member_documents)

        # Serialize documents
        ser_directorate = TinyProjectDocumentSerializerWithUserDocsBelongTo(
            directorate_documents,
            many=True,
            context={"request": request, "for_user": None},
        )

        # BA documents - serialize for each BA leader
        ba_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.business_areas_led.exists():
                user_ba_areas = assignment.user.business_areas_led.values_list(
                    "id", flat=True
                )
                user_ba_documents = ba_documents.filter(
                    project__business_area__in=user_ba_areas
                )

                ser = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_ba_documents,
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                ba_serialized.extend(ser.data)

        # Lead documents - serialize for each project lead
        lead_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in project_lead_user_ids:
                user_lead_projects = ProjectMember.objects.filter(
                    user=assignment.user, is_leader=True
                ).values_list("project_id", flat=True)

                user_lead_documents = lead_documents.filter(
                    project__in=user_lead_projects
                )

                ser = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_lead_documents,
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                lead_serialized.extend(ser.data)

        # Team member documents - serialize for each team member
        member_serialized = []
        for assignment in caretaker_assignments:
            if assignment.user.id in team_member_user_ids:
                user_team_projects = ProjectMember.objects.filter(
                    user=assignment.user, is_leader=False, project__in=active_projects
                ).values_list("project_id", flat=True)

                user_member_documents = member_documents.filter(
                    project__in=user_team_projects
                )

                ser = TinyProjectDocumentSerializerWithUserDocsBelongTo(
                    user_member_documents,
                    many=True,
                    context={"request": request, "for_user": assignment.user},
                )
                member_serialized.extend(ser.data)

        # Combine all serialized data and remove duplicates
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


# endregion


# region Utility Views


class CheckCaretaker(APIView):
    """Check if user has caretaker or is caretaking"""
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
            secondary_users__contains=[user.pk],
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
        )
        
        # Auto-cancel expired pending requests
        if caretaker_request_object.exists():
            request = caretaker_request_object.first()
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


class AdminSetCaretaker(APIView):
    """Admin endpoint to directly set a caretaker"""
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
        if secondary_user.caretakers.exists():
            return Response(
                {"detail": "Cannot set a user with a caretaker as caretaker."},
                status=HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            Caretaker.objects.create(
                user=primary_user,
                caretaker=secondary_user,
                reason=reason,
                end_date=end_date if end_date else None,
                notes=notes if notes else None,
            )

        return Response(status=HTTP_200_OK)


# endregion
