"""
Area type views - List areas by type
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK

from locations.services import AreaService
from locations.serializers import TinyAreaSerializer


class DBCADistricts(APIView):
    """List DBCA districts"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all DBCA districts"""
        areas = AreaService.list_areas(area_type="dbcadistrict")
        serializer = TinyAreaSerializer(areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class DBCARegions(APIView):
    """List DBCA regions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all DBCA regions"""
        areas = AreaService.list_areas(area_type="dbcaregion")
        serializer = TinyAreaSerializer(areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class Imcras(APIView):
    """List IMCRA areas"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all IMCRA areas"""
        areas = AreaService.list_areas(area_type="imcra")
        serializer = TinyAreaSerializer(areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class Ibras(APIView):
    """List IBRA areas"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all IBRA areas"""
        areas = AreaService.list_areas(area_type="ibra")
        serializer = TinyAreaSerializer(areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class Nrms(APIView):
    """List NRM areas"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all NRM areas"""
        areas = AreaService.list_areas(area_type="nrm")
        serializer = TinyAreaSerializer(areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
