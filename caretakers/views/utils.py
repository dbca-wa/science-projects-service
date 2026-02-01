"""
Utility views for caretaker operations
"""
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

from adminoptions.serializers import AdminTaskSerializer
from ..serializers import CaretakerSerializer
from ..services import CaretakerService, CaretakerRequestService


class CheckCaretaker(APIView):
    """Check if user has caretaker or is caretaking"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check caretaker status for current user"""
        settings.LOGGER.info(f"{request.user} is checking caretaker status")
        
        user = request.user
        
        # Get caretaker object
        caretaker_object = CaretakerService.get_user_caretaker(user)
        
        # Get pending requests
        requests = CaretakerRequestService.get_user_requests(user)
        
        return Response(
            {
                "caretaker_object": (
                    CaretakerSerializer(caretaker_object).data
                    if caretaker_object
                    else None
                ),
                "caretaker_request_object": (
                    AdminTaskSerializer(requests['caretaker_request']).data
                    if requests['caretaker_request']
                    else None
                ),
                "become_caretaker_request_object": (
                    AdminTaskSerializer(requests['become_caretaker_request']).data
                    if requests['become_caretaker_request']
                    else None
                ),
            },
            status=HTTP_200_OK,
        )


class AdminSetCaretaker(APIView):
    """Admin endpoint to directly set a caretaker"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Admin creates caretaker relationship directly"""
        settings.LOGGER.info(f"{request.user} is setting a caretaker (admin)")
        
        if not request.user.is_superuser:
            return Response(
                {"detail": "You do not have permission to set a caretaker."},
                status=HTTP_401_UNAUTHORIZED,
            )
        
        primary_user_id = request.data.get("userPk")
        secondary_user_id = request.data.get("caretakerPk")
        reason = request.data.get("reason")
        end_date = request.data.get("endDate")
        notes = request.data.get("notes")
        
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
        
        try:
            CaretakerService.create_caretaker(
                user=primary_user_id,
                caretaker=secondary_user_id,
                reason=reason,
                end_date=end_date if end_date else None,
                notes=notes if notes else None,
            )
            return Response(status=HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )
