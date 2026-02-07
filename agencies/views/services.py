# region IMPORTS ====================================================================================================
from django.conf import settings
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from ..models import DepartmentalService
from ..serializers import (
    DepartmentalServiceSerializer,
    TinyDepartmentalServiceSerializer,
)
from ..services.agency_service import AgencyService

# endregion  =================================================================================================


class DepartmentalServices(APIView):
    """List and create departmental services"""

    def get(self, request):
        services = DepartmentalService.objects.all()
        serializer = TinyDepartmentalServiceSerializer(services, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a departmental service")
        serializer = DepartmentalServiceSerializer(data=request.data)

        if serializer.is_valid():
            service = serializer.save()
            return Response(
                TinyDepartmentalServiceSerializer(service).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class DepartmentalServiceDetail(APIView):
    """Retrieve, update, and delete departmental service"""

    def get(self, request, pk):
        service = AgencyService.get_departmental_service(pk)
        serializer = DepartmentalServiceSerializer(service)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        service = AgencyService.get_departmental_service(pk)
        settings.LOGGER.info(
            f"{request.user} is updating departmental service detail {service}"
        )

        serializer = DepartmentalServiceSerializer(
            service,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            updated_service = serializer.save()
            return Response(
                TinyDepartmentalServiceSerializer(updated_service).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        service = AgencyService.get_departmental_service(pk)
        settings.LOGGER.info(
            f"{request.user} is deleting departmental service detail {service}"
        )
        service.delete()
        return Response(status=HTTP_204_NO_CONTENT)
