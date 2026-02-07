"""
Custom publication views
"""

from django.conf import settings
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from ..models import CustomPublication
from ..serializers import CustomPublicationSerializer


class CustomPublications(APIView):
    """List and create custom publications"""

    def get(self, request):
        """List all custom publications"""
        settings.LOGGER.info(f"{request.user} is getting CustomPublications")
        custom_publications = CustomPublication.objects.all()
        serializer = CustomPublicationSerializer(custom_publications, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create a new custom publication"""
        settings.LOGGER.info(f"{request.user} is creating a CustomPublication")

        serializer = CustomPublicationSerializer(data=request.data)

        if not serializer.is_valid():
            settings.LOGGER.error(
                f"Error creating CustomPublication: {serializer.errors}"
            )
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)


class CustomPublicationDetail(APIView):
    """Get, update, and delete custom publications"""

    def get(self, request, pk):
        """Get custom publication by ID"""
        settings.LOGGER.info(f"{request.user} is getting CustomPublication {pk}")

        try:
            obj = CustomPublication.objects.get(pk=pk)
        except CustomPublication.DoesNotExist:
            raise NotFound

        serializer = CustomPublicationSerializer(obj)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update custom publication"""
        settings.LOGGER.info(f"{request.user} is updating CustomPublication {pk}")

        try:
            obj = CustomPublication.objects.get(pk=pk)
        except CustomPublication.DoesNotExist:
            raise NotFound

        public_profile = obj.public_profile
        title = request.data.get("title")
        year = request.data.get("year")

        serializer = CustomPublicationSerializer(
            obj,
            data={"title": title, "year": year, "public_profile": public_profile.pk},
        )

        if not serializer.is_valid():
            settings.LOGGER.error(
                f"Error updating CustomPublication: {serializer.errors}"
            )
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)

    def delete(self, request, pk):
        """Delete custom publication"""
        settings.LOGGER.info(f"{request.user} is deleting CustomPublication {pk}")

        try:
            obj = CustomPublication.objects.get(pk=pk)
        except CustomPublication.DoesNotExist:
            raise NotFound

        obj.delete()
        return Response(status=HTTP_204_NO_CONTENT)
