"""
Views for caretaker request management (AdminTask integration)
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
)

from adminoptions.serializers import AdminTaskSerializer
from ..serializers import CaretakerSerializer
from ..services import CaretakerRequestService


class CaretakerRequestList(APIView):
    """Get pending caretaker requests for a user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all pending caretaker requests where user is being asked to be caretaker"""
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response(
                {"error": "user_id query parameter is required"},
                status=HTTP_400_BAD_REQUEST,
            )
        
        settings.LOGGER.info(
            f"{request.user} is getting pending caretaker requests for user {user_id}"
        )
        
        pending_requests = CaretakerRequestService.get_pending_requests_for_user(user_id)
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
