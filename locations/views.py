from rest_framework.exceptions import (
    NotFound,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import render
from django.db import transaction
from django.conf import settings
from django.utils import timezone

import time

from .models import Area
from .serializers import (
    TinyAreaSerializer,
    AreaSerializer,
)

# GET ONLY ======================================================================


class DBCADistricts(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = Area.objects.filter(area_type="dbcadistrict").all()
        ser = TinyAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class DBCARegions(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = Area.objects.filter(area_type="dbcaregion").all()
        ser = TinyAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class Imcras(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = Area.objects.filter(area_type="imcra").all()
        ser = TinyAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class Ibras(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = Area.objects.filter(area_type="ibra").all()
        ser = TinyAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class Nrms(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = Area.objects.filter(area_type="nrm").all()
        ser = TinyAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


# MAIN ======================================================================


class Areas(APIView):
    def get(self, req):
        all = Area.objects.all()
        ser = TinyAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = AreaSerializer(
            data=req.data,
        )
        if ser.is_valid():
            area = ser.save()
            return Response(
                TinyAreaSerializer(area).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AreaDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = Area.objects.get(pk=pk)
        except Area.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        area = self.go(pk)
        ser = AreaSerializer(area)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        area = self.go(pk)
        area.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        area = self.go(pk)
        ser = AreaSerializer(
            area,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_area = ser.save()
            return Response(
                TinyAreaSerializer(updated_area).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )
