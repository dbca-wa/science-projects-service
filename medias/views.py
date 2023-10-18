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
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import render
from django.db import transaction
from django.conf import settings
from django.utils import timezone

import requests
import time

from .models import (
    AgencyImage,
    AnnualReportMedia,
    BusinessAreaPhoto,
    ProjectDocumentPDF,
    ProjectPhoto,
    UserAvatar,
)
from .serializers import (
    AgencyPhotoSerializer,
    AnnualReportMediaSerializer,
    BusinessAreaPhotoSerializer,
    ProjectDocumentPDFSerializer,
    ProjectPhotoSerializer,
    TinyAgencyPhotoSerializer,
    TinyAnnualReportMediaSerializer,
    TinyBusinessAreaPhotoSerializer,
    TinyProjectPhotoSerializer,
    TinyUserAvatarSerializer,
    UserAvatarSerializer,
)

# PROJECT DOCS ==================================================================================================


class ProjectDocPDFS(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = ProjectDocumentPDF.objects.all()
        ser = ProjectDocumentPDFSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = ProjectDocumentPDFSerializer(
            data=req.data,
        )
        if ser.is_valid():
            ser = ser.save()
            return Response(
                TinyAnnualReportMediaSerializer(ser).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


# https://scienceprojects.dbca.wa.gov.au/media/ararreports/12/AnnualReport20222023_25.pdf

# ANNUAL REPORT ==================================================================================================


class AnnualReportMedias(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = AnnualReportMedia.objects.all()
        ser = TinyAnnualReportMediaSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = AnnualReportMediaSerializer(
            data=req.data,
        )
        if ser.is_valid():
            reportmedia = ser.save()
            return Response(
                TinyAnnualReportMediaSerializer(reportmedia).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class AnnualReportMediaDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = AnnualReportMedia.objects.get(pk=pk)
        except AnnualReportMedia.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        reportmedia = self.go(pk)
        ser = AnnualReportMediaSerializer(
            reportmedia,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        reportmedia = self.go(pk)
        reportmedia.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        reportmedia = self.go(pk)
        ser = AnnualReportMediaSerializer(
            reportmedia,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_reportmedia = ser.save()
            return Response(
                TinyAnnualReportMediaSerializer(u_reportmedia).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# BUSINESS AREAS ==================================================================================================


class BusinessAreaPhotos(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = BusinessAreaPhoto.objects.all()
        ser = TinyBusinessAreaPhotoSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = BusinessAreaPhotoSerializer(
            data=req.data,
        )
        if ser.is_valid():
            ba_photo = ser.save()
            return Response(
                TinyBusinessAreaPhotoSerializer(ba_photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class BusinessAreaPhotoDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = BusinessAreaPhoto.objects.get(pk=pk)
        except BusinessAreaPhoto.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        ba_photo = self.go(pk)
        ser = BusinessAreaPhotoSerializer(
            ba_photo,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        business_photo = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (business_photo.uploader == req.user or req.user.is_superuser):
            raise PermissionDenied

        business_photo.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        business_photo = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (business_photo.uploader == req.user or req.user.is_superuser):
            raise PermissionDenied

        ser = BusinessAreaPhotoSerializer(
            business_photo,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_business_photo = ser.save()
            return Response(
                TinyBusinessAreaPhotoSerializer(u_business_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# PROJECTS ==================================================================================================


class ProjectPhotos(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = ProjectPhoto.objects.all()
        ser = TinyProjectPhotoSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = ProjectPhotoSerializer(
            data=req.data,
        )
        if ser.is_valid():
            ba_photo = ser.save()
            return Response(
                TinyProjectPhotoSerializer(ba_photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class ProjectPhotoDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectPhoto.objects.get(pk=pk)
        except ProjectPhoto.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        project_photo = self.go(pk)
        ser = ProjectPhotoSerializer(
            project_photo,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        project_photo = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (project_photo.uploader == req.user or req.user.is_superuser):
            raise PermissionDenied

        project_photo.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        project_photo = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (project_photo.uploader == req.user or req.user.is_superuser):
            raise PermissionDenied

        ser = ProjectPhotoSerializer(
            project_photo,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_project_photo = ser.save()
            return Response(
                TinyProjectPhotoSerializer(u_project_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# AGENCIES ==================================================================================================


class AgencyPhotos(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = AgencyImage.objects.all()
        ser = TinyAgencyPhotoSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = ProjectPhotoSerializer(
            data=req.data,
        )
        if ser.is_valid():
            agency_photo = ser.save()
            return Response(
                TinyAgencyPhotoSerializer(agency_photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class AgencyPhotoDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AgencyImage.objects.get(pk=pk)
        except AgencyImage.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        agency_photo = self.go(pk)
        ser = AgencyPhotoSerializer(
            agency_photo,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        agency_photo = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser):
            raise PermissionDenied

        agency_photo.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        agency_photo = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser):
            raise PermissionDenied

        ser = AgencyPhotoSerializer(
            agency_photo,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_agency_photo = ser.save()
            return Response(
                TinyAgencyPhotoSerializer(u_agency_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# USER AVATARS ==================================================================================================


class UserAvatars(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = UserAvatar.objects.all()
        ser = TinyUserAvatarSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        ser = UserAvatarSerializer(
            data=req.data,
        )
        if ser.is_valid():
            user_avatar = ser.save()
            return Response(
                TinyUserAvatarSerializer(user_avatar).data,
                status=HTTP_201_CREATED,
            )
        else:
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class UserAvatarDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = UserAvatar.objects.get(pk=pk)
        except UserAvatar.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        user_avatar = self.go(pk)
        ser = UserAvatarSerializer(
            user_avatar,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        user_avatar = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser or req.user == user_avatar.user):
            raise PermissionDenied

        user_avatar.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        user_avatar = self.go(pk)

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser or req.user == user_avatar.user):
            raise PermissionDenied

        ser = UserAvatarSerializer(
            user_avatar,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_user_avatar = ser.save()
            return Response(
                TinyUserAvatarSerializer(u_user_avatar).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# HELPERS ==================================================================================================


class GetUploadURL(APIView):
    pass
    # def post(self, req):
    #     # UPDATE WITH AZURE STYLE
    #     # pass
    #     # # f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ID}/images/v1"

    #     url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/images/v2/direct_upload"
    #     one_time_url = requests.post(
    #         url,
    #         headers={
    #             "Authorization": f"Bearer {settings.CF_IMAGES_TOKEN}",
    #             # "Content-Type": "multipart/form-data",
    #         },
    #     )
    #     one_time_url = one_time_url.json()
    #     result = one_time_url.get("result")
    #     print(result)
    #     return Response(
    #         {
    #             "uploadURL": result.get("uploadURL"),
    #         }
    #     )


# ==================================================================================================
