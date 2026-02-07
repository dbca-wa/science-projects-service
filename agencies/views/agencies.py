# region IMPORTS ====================================================================================================
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from ..models import Agency
from ..serializers import AgencySerializer, TinyAgencySerializer
from ..services.agency_service import AgencyService

# endregion  =================================================================================================


class Agencies(APIView):
    """List and create agencies"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        agencies = Agency.objects.all()
        serializer = TinyAgencySerializer(agencies, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting an agency")
        serializer = AgencySerializer(data=request.data)

        if serializer.is_valid():
            agency = serializer.save()
            return Response(
                TinyAgencySerializer(agency).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class AgencyDetail(APIView):
    """Retrieve, update, and delete agency"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        agency = AgencyService.get_agency(pk)
        serializer = AgencySerializer(agency)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        agency = AgencyService.get_agency(pk)
        settings.LOGGER.info(f"{request.user} is updating {agency}")

        serializer = AgencySerializer(
            agency,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            updated_agency = serializer.save()
            return Response(
                TinyAgencySerializer(updated_agency).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        agency = AgencyService.get_agency(pk)
        settings.LOGGER.info(f"{request.user} is deleting agency {agency}")
        agency.delete()
        return Response(status=HTTP_204_NO_CONTENT)
