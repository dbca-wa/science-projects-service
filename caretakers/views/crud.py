"""
CRUD views for caretaker relationships
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from ..serializers import CaretakerSerializer, CaretakerCreateSerializer
from ..services import CaretakerService


class CaretakerList(APIView):
    """List all caretaker relationships or create new one"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all caretaker relationships"""
        settings.LOGGER.info(f"{request.user} is getting all caretakers")
        
        caretakers = CaretakerService.list_caretakers()
        serializer = CaretakerSerializer(caretakers, many=True)
        
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new caretaker relationship"""
        settings.LOGGER.info(f"{request.user} is creating a caretaker relationship")
        
        serializer = CaretakerCreateSerializer(data=request.data)
        if not serializer.is_valid():
            settings.LOGGER.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        caretaker = serializer.save()
        result_serializer = CaretakerSerializer(caretaker)
        
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class CaretakerDetail(APIView):
    """Get, update, or delete a caretaker relationship"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get caretaker relationship details"""
        caretaker = CaretakerService.get_caretaker(pk)
        serializer = CaretakerSerializer(caretaker)
        
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update caretaker relationship"""
        settings.LOGGER.info(f"{request.user} is updating caretaker {pk}")
        
        serializer = CaretakerSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            settings.LOGGER.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        caretaker = CaretakerService.update_caretaker(pk, serializer.validated_data)
        result_serializer = CaretakerSerializer(caretaker)
        
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete caretaker relationship"""
        CaretakerService.delete_caretaker(pk, request.user)
        
        return Response(status=HTTP_204_NO_CONTENT)
