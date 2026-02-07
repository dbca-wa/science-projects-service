"""
Views for caretaker request management (AdminTask integration)
"""

from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView

from adminoptions.serializers import AdminTaskSerializer
from users.models import User

from ..serializers import CaretakerSerializer
from ..services import CaretakerRequestService


class CaretakerRequestList(APIView):
    """Get pending caretaker requests for a user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all pending caretaker requests where user is being asked to be caretaker"""
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"error": "user_id query parameter is required"},
                status=HTTP_400_BAD_REQUEST,
            )

        settings.LOGGER.info(
            f"{request.user} is getting pending caretaker requests for user {user_id}"
        )

        pending_requests = CaretakerRequestService.get_pending_requests_for_user(
            user_id
        )
        serializer = AdminTaskSerializer(pending_requests, many=True)

        return Response(serializer.data, status=HTTP_200_OK)


class ApproveCaretakerRequest(APIView):
    """Approve a caretaker request"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Approve caretaker request"""
        caretaker = CaretakerRequestService.approve_request(pk, request.user)

        return Response(
            {
                "message": "Caretaker request approved successfully",
                "caretaker": CaretakerSerializer(caretaker).data,
            },
            status=HTTP_202_ACCEPTED,
        )


class RejectCaretakerRequest(APIView):
    """Reject a caretaker request"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Reject caretaker request"""
        CaretakerRequestService.reject_request(pk, request.user)

        return Response(
            {"message": "Caretaker request rejected successfully"},
            status=HTTP_202_ACCEPTED,
        )


class CaretakerRequestCreate(APIView):
    """Create a new caretaker request"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create caretaker request"""
        # Validate input
        user_id = request.data.get("user_id")
        caretaker_id = request.data.get("caretaker_id")
        approve_immediately = request.data.get("approve_immediately", False)

        if not user_id or not caretaker_id:
            return Response(
                {"error": "user_id and caretaker_id are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Validate approve_immediately permission
        if approve_immediately and not request.user.is_superuser:
            return Response(
                {"error": "Only superusers can approve requests immediately"},
                status=HTTP_403_FORBIDDEN,
            )

        try:
            # Create request via service
            task = CaretakerRequestService.create_request(
                requester=request.user,
                user_id=user_id,
                caretaker_id=caretaker_id,
                reason=request.data.get("reason"),
                end_date=request.data.get("end_date"),
                notes=request.data.get("notes"),
            )

            # If approve_immediately is True, approve the request immediately
            if approve_immediately:
                caretaker = CaretakerRequestService.approve_request(
                    task.id, request.user
                )
                return Response(
                    {
                        "task_id": task.id,
                        "approved": True,
                        "caretaker": CaretakerSerializer(caretaker).data,
                    },
                    status=HTTP_201_CREATED,
                )

            # Serialize and return
            serializer = AdminTaskSerializer(task)
            return Response(
                {
                    "task_id": task.id,
                    "task": serializer.data,
                },
                status=HTTP_201_CREATED,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=HTTP_400_BAD_REQUEST,
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )


class CaretakerRequestCancel(APIView):
    """Cancel a caretaker request"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Cancel caretaker request"""
        try:
            CaretakerRequestService.cancel_request(pk, request.user)

            return Response(
                {"message": "Caretaker request cancelled successfully"},
                status=HTTP_202_ACCEPTED,
            )

        except NotFound as e:
            return Response(
                {"error": str(e)},
                status=HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as e:
            return Response(
                {"error": str(e)},
                status=HTTP_403_FORBIDDEN,
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )


class CaretakerOutgoingRequestList(APIView):
    """Get outgoing caretaker requests for a user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all pending caretaker requests where user is primary_user"""
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"error": "user_id query parameter is required"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Verify user can only see their own requests (unless admin)
        if not request.user.is_superuser and str(request.user.id) != str(user_id):
            return Response(
                {"error": "You can only view your own requests"},
                status=HTTP_403_FORBIDDEN,
            )

        settings.LOGGER.info(
            f"{request.user} is getting outgoing caretaker requests for user {user_id}"
        )

        outgoing_requests = CaretakerRequestService.get_outgoing_requests_for_user(
            user_id
        )
        serializer = AdminTaskSerializer(outgoing_requests, many=True)

        return Response(serializer.data, status=HTTP_200_OK)
