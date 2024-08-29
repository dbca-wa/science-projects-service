# region IMPORTS ==================================================================================================

from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticated
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

# Project imports --------------------

from documents.models import AnnualReport
from .models import (
    AgencyImage,
    AnnualReportMedia,
    AnnualReportPDF,
    BusinessAreaPhoto,
    LegacyAnnualReportPDF,
    ProjectDocumentPDF,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
    UserAvatar,
)
from .serializers import (
    AgencyPhotoSerializer,
    AnnualReportMediaCreationSerializer,
    AnnualReportMediaSerializer,
    AnnualReportPDFCreateSerializer,
    AnnualReportPDFSerializer,
    BusinessAreaPhotoSerializer,
    LegacyAnnualReportPDFCreateSerializer,
    LegacyAnnualReportPDFSerializer,
    MethodologyImageCreateSerializer,
    MethodologyImageSerializer,
    ProjectDocumentPDFSerializer,
    ProjectPhotoSerializer,
    TinyAgencyPhotoSerializer,
    TinyAnnualReportMediaSerializer,
    TinyAnnualReportPDFSerializer,
    TinyBusinessAreaPhotoSerializer,
    TinyLegacyAnnualReportPDFSerializer,
    TinyMethodologyImageSerializer,
    TinyProjectPhotoSerializer,
    TinyUserAvatarSerializer,
    UserAvatarSerializer,
)

# endregion ========================================================================================================

# region PROJECT DOCS ==================================================================================================


class ProjectDocPDFS(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(msg=f"{req.user} is posting a project document pdf")
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


# endregion ========================================================================================================

# region ANNUAL REPORT ==================================================================================================


class AnnualReportPDFs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = AnnualReportPDF.objects.all()
        ser = TinyAnnualReportPDFSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting an annual report pdf")
        file = req.FILES.get("file")
        report_id = req.data.get("report")

        data = {
            "file": file,
            "report": report_id,
            "creator": req.user.pk,
        }
        new_instance = AnnualReportPDFCreateSerializer(data=data)
        if new_instance.is_valid():
            saved_instance = new_instance.save()
            return Response(
                TinyAnnualReportPDFSerializer(saved_instance).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{new_instance.errors}")
            return Response(
                new_instance.errors,
                HTTP_400_BAD_REQUEST,
            )


class LegacyAnnualReportPDFs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = LegacyAnnualReportPDF.objects.all()
        ser = TinyLegacyAnnualReportPDFSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a legacy annual report pdf")
        file = req.FILES.get("file")
        year = req.data.get("year")

        data = {
            "file": file,
            "year": year,
            "creator": req.user.pk,
        }
        new_instance = LegacyAnnualReportPDFCreateSerializer(data=data)
        if new_instance.is_valid():
            saved_instance = new_instance.save()
            return Response(
                TinyLegacyAnnualReportPDFSerializer(saved_instance).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{new_instance.errors}")
            return Response(
                new_instance.errors,
                HTTP_400_BAD_REQUEST,
            )


class AnnualReportPDFDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AnnualReportPDF.objects.get(pk=pk)
        except AnnualReportPDF.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        reportmedia = self.go(pk)
        ser = AnnualReportPDFSerializer(
            reportmedia,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        reportmedia = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting annual report media detail {reportmedia}"
        )
        reportmedia.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        reportmedia = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating annual report media detail {reportmedia}"
        )
        ser = AnnualReportPDFSerializer(
            reportmedia,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_reportmedia = ser.save()
            return Response(
                TinyAnnualReportPDFSerializer(u_reportmedia).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class LegacyAnnualReportPDFDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = LegacyAnnualReportPDF.objects.get(pk=pk)
        except LegacyAnnualReportPDF.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        reportmedia = self.go(pk)
        ser = LegacyAnnualReportPDFSerializer(
            reportmedia,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        reportmedia = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting legacy annual report detail {reportmedia}"
        )
        reportmedia.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        reportmedia = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating legacy annual report detail {reportmedia}"
        )
        ser = LegacyAnnualReportPDFSerializer(
            reportmedia,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_reportmedia = ser.save()
            return Response(
                TinyLegacyAnnualReportPDFSerializer(u_reportmedia).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AnnualReportMedias(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(msg=f"{req.user} is posting annual report media")
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class AnnualReportMediaDetail(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(
            msg=f"{req.user} is deleting annual report media detail {reportmedia}"
        )
        reportmedia.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        reportmedia = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating annual report media detail {reportmedia}"
        )
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class LatestReportMedia(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        settings.LOGGER.info(msg=f"{req.user} is getting latest report's media")

        def go():
            try:
                latest = AnnualReport.objects.order_by("-year").first()
                medias = AnnualReportMedia.objects.filter(report=latest).all()
                return TinyAnnualReportMediaSerializer(medias, many=True)
            except AnnualReportMedia.DoesNotExist:
                print("MEDIA OBJECT NOT FOUND")
                raise NotFound
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise e

        this_reports_media = go()
        return Response(
            this_reports_media.data,
            status=HTTP_200_OK,
        )


class AnnualReportMediaUpload(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req, pk):
        def go(pk):
            try:
                medias = AnnualReportMedia.objects.filter(report=pk).all()
                return TinyAnnualReportMediaSerializer(medias, many=True)
            except AnnualReportMedia.DoesNotExist:
                raise NotFound
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise e

        this_reports_media = go(pk)
        return Response(
            this_reports_media.data,
            status=HTTP_200_OK,
        )

    def post(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is posting a report media upload")

        def get_report(pk):
            try:
                report = get_object_or_404(AnnualReport, pk=pk)
                return report
            except AnnualReport.DoesNotExist:
                settings.LOGGER.error(msg=f"{e}")
                raise NotFound
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise e

        def get_image_of_section(section, report):
            return AnnualReportMedia.objects.filter(report=report, kind=section).first()

        section = req.data["section"]
        file = req.data["file"]

        report = get_report(pk)
        image_instance = get_image_of_section(section, report)

        if image_instance:
            # If an instance exists, update the file
            image_instance.file = file
            image_instance.uploader = req.user
            updated = image_instance.save()
            updated_ser = AnnualReportMediaSerializer(updated)
            return Response(
                updated_ser.data,
                status=HTTP_202_ACCEPTED,
            )

        else:
            # If no instance exists, create a new one
            new_instance_data = {
                "kind": section,
                "file": file,
                "report": report.pk,
                "uploader": req.user.pk,
            }
            serializer = AnnualReportMediaCreationSerializer(data=new_instance_data)
            if serializer.is_valid():
                updated = serializer.save()
                ser = AnnualReportMediaSerializer(updated).data
                return Response(ser, HTTP_201_CREATED)
            else:
                settings.LOGGER.error(msg=f"{serializer.errors}")
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    permission_classes = [IsAuthenticated]


class AnnualReportMediaDelete(APIView):
    def go(self, pk, section):
        try:
            object = AnnualReportMedia.objects.filter(report=pk, kind=section).first()
        except AnnualReportMedia.DoesNotExist:
            raise NotFound
        return object

    def delete(self, req, pk, section):
        settings.LOGGER.info(
            msg=f"{req.user} is deleting annual report media with pk {pk}"
        )
        object = self.go(pk, section)
        object.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )


# endregion ========================================================================================================

# region BUSINESS AREAS ==================================================================================================


class BusinessAreaPhotos(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(msg=f"{req.user} is posting a business area photo")
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
            settings.LOGGER.error(msg=f"{ser.errors}")
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
        settings.LOGGER.info(
            msg=f"{req.user} is deleting a business area photo {business_photo}"
        )

        # Check if the user is an admin or the uploader of the photo
        if not (business_photo.uploader == req.user or req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} doesn't have permission to delete {business_photo}"
            )
            raise PermissionDenied

        business_photo.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        business_photo = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating a business area photo {business_photo}"
        )

        # Check if the user is an admin or the uploader of the photo
        if not (business_photo.uploader == req.user or req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} deosn't have permission to update {business_photo}"
            )
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion ========================================================================================================

# region PROJECTS ==================================================================================================


class ProjectPhotos(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(msg=f"{req.user} is posting a project photo")
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
            settings.LOGGER.info(msg=f"{ser.errors}")
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
        settings.LOGGER.info(
            msg=f"{req.user} is deleting project photo {project_photo}"
        )

        # Check if the user is an admin or the uploader of the photo
        if not (project_photo.uploader == req.user or req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} is not allowed to delete project photo {project_photo}"
            )
            raise PermissionDenied

        project_photo.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        project_photo = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating project photo {project_photo}"
        )

        # Check if the user is an admin or the uploader of the photo
        if not (project_photo.uploader == req.user or req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} is not allowed to update project photo {project_photo}"
            )
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class MethodologyPhotos(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = ProjectPlanMethodologyPhoto.objects.all()
        ser = TinyMethodologyImageSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is uploading a newmethodology photo")

        project_plan = req.data["pk"]
        file = req.data["file"]

        ser = MethodologyImageCreateSerializer(
            data={
                "project_plan": int(project_plan),
                "file": file,
                "uploader": req.user.pk,
            },
        )
        if ser.is_valid():
            ba_photo = ser.save()
            return Response(
                TinyMethodologyImageSerializer(ba_photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.info(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class MethodologyPhotoDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = ProjectPlanMethodologyPhoto.objects.get(project_plan=pk)
        except ProjectPlanMethodologyPhoto.DoesNotExist:
            return None
        return obj

    def get(self, req, pk):
        obj = self.go(pk=pk)
        ser = MethodologyImageSerializer(
            obj,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req, pk):
        obj = self.go(pk=pk)
        settings.LOGGER.info(msg=f"{req.user} is updating methodology photo {obj}")

        # Check if the user is an admin or the uploader of the photo
        if not (obj.uploader == req.user or req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} is not allowed to update methodology photo {obj}"
            )
            raise PermissionDenied

        ser = MethodologyImageSerializer(
            obj,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_photo = ser.save()
            return Response(
                TinyMethodologyImageSerializer(u_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )

    def delete(self, req, pk):
        obj = self.go(pk=pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting methodology photo {obj}")

        # Check if the user is an admin or the uploader of the photo
        if not (obj.uploader == req.user or req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} is not allowed to delete project photo {obj}"
            )
            raise PermissionDenied

        obj.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )


# endregion ========================================================================================================

# region AGENCIES ==================================================================================================


class AgencyPhotos(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(msg=f"{req.user} is posting an agency photo")
        ser = AgencyPhotoSerializer(
            data=req.data,
        )
        if ser.is_valid():
            agency_photo = ser.save(image=req.data["image"])
            return Response(
                TinyAgencyPhotoSerializer(agency_photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
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
        settings.LOGGER.info(msg=f"{req.user} is deleting agency photo {agency_photo}")

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} cannot delete {agency_photo} as they are not a superuser"
            )
            raise PermissionDenied

        agency_photo.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        agency_photo = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating agency photo {agency_photo}")

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser):
            settings.LOGGER.warning(
                msg=f"{req.user} cannot udpate {agency_photo} as they are not a superuser"
            )
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion ========================================================================================================

# region USER AVATARS ==================================================================================================


class UserAvatars(APIView):
    permission_classes = [IsAuthenticated]

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
        settings.LOGGER.info(msg=f"{req.user} is posting a user avatar")
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
            settings.LOGGER.error(msg=f"{ser.errors}")
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
        settings.LOGGER.info(msg=f"{req.user} is deleting user avatar {user_avatar}")

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser or req.user == user_avatar.user):
            settings.LOGGER.warning(
                msg=f"Permission denied as {req.user} is not superuser and isn't the avatar owner of {user_avatar}"
            )
            raise PermissionDenied

        user_avatar.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        user_avatar = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating user avatar {user_avatar}")

        # Check if the user is an admin or the uploader of the photo
        if not (req.user.is_superuser or req.user == user_avatar.user):
            settings.LOGGER.warning(
                msg=f"Permission denied as {req.user} is not superuser and isn't the avatar owner of {user_avatar}"
            )
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
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion ========================================================================================================
