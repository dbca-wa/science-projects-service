# region IMPORTS ==================================================================================================
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
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

from documents.models import AnnualReport

from ..models import AnnualReportMedia
from ..serializers import (
    AnnualReportMediaCreationSerializer,
    AnnualReportMediaSerializer,
    AnnualReportPDFCreateSerializer,
    AnnualReportPDFSerializer,
    LegacyAnnualReportPDFCreateSerializer,
    LegacyAnnualReportPDFSerializer,
    TinyAnnualReportMediaSerializer,
    TinyAnnualReportPDFSerializer,
    TinyLegacyAnnualReportPDFSerializer,
)
from ..services.media_service import MediaService

# endregion ========================================================================================================


class AnnualReportPDFs(APIView):
    """List and create annual report PDFs"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        pdfs = MediaService.list_annual_report_pdfs()
        serializer = TinyAnnualReportPDFSerializer(
            pdfs, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting an annual report pdf")

        file = request.FILES.get("file")
        report_id = request.data.get("report")
        data = {
            "file": file,
            "report": report_id,
            "creator": request.user.pk,
        }

        serializer = AnnualReportPDFCreateSerializer(data=data)
        if serializer.is_valid():
            saved_instance = serializer.save()
            return Response(
                TinyAnnualReportPDFSerializer(saved_instance).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class AnnualReportPDFDetail(APIView):
    """Retrieve, update, and delete annual report PDF"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pdf = MediaService.get_annual_report_pdf(pk)
        serializer = AnnualReportPDFSerializer(pdf, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        pdf = MediaService.get_annual_report_pdf(pk)
        settings.LOGGER.info(f"{request.user} is updating annual report PDF {pdf}")

        serializer = AnnualReportPDFSerializer(pdf, data=request.data, partial=True)
        if serializer.is_valid():
            updated_pdf = serializer.save()
            return Response(
                TinyAnnualReportPDFSerializer(updated_pdf).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        MediaService.delete_annual_report_pdf(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class LegacyAnnualReportPDFs(APIView):
    """List and create legacy annual report PDFs"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        pdfs = MediaService.list_legacy_annual_report_pdfs()
        serializer = TinyLegacyAnnualReportPDFSerializer(
            pdfs, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a legacy annual report pdf")

        file = request.FILES.get("file")
        year = request.data.get("year")
        data = {
            "file": file,
            "year": year,
            "creator": request.user.pk,
        }

        serializer = LegacyAnnualReportPDFCreateSerializer(data=data)
        if serializer.is_valid():
            saved_instance = serializer.save()
            return Response(
                TinyLegacyAnnualReportPDFSerializer(saved_instance).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class LegacyAnnualReportPDFDetail(APIView):
    """Retrieve, update, and delete legacy annual report PDF"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pdf = MediaService.get_legacy_annual_report_pdf(pk)
        serializer = LegacyAnnualReportPDFSerializer(pdf, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        pdf = MediaService.get_legacy_annual_report_pdf(pk)
        settings.LOGGER.info(
            f"{request.user} is updating legacy annual report PDF {pdf}"
        )

        serializer = LegacyAnnualReportPDFSerializer(
            pdf, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated_pdf = serializer.save()
            return Response(
                TinyLegacyAnnualReportPDFSerializer(updated_pdf).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        MediaService.delete_legacy_annual_report_pdf(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class AnnualReportMedias(APIView):
    """List and create annual report media"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        media = MediaService.list_annual_report_media()
        serializer = TinyAnnualReportMediaSerializer(
            media, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting annual report media")
        serializer = AnnualReportMediaCreationSerializer(data=request.data)

        if serializer.is_valid():
            media = serializer.save()
            return Response(
                TinyAnnualReportMediaSerializer(media).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class AnnualReportMediaDetail(APIView):
    """Retrieve, update, and delete annual report media"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        media = MediaService.get_annual_report_media(pk)
        serializer = AnnualReportMediaSerializer(media, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        media = MediaService.get_annual_report_media(pk)
        settings.LOGGER.info(f"{request.user} is updating annual report media {media}")

        serializer = AnnualReportMediaSerializer(media, data=request.data, partial=True)
        if serializer.is_valid():
            updated_media = serializer.save()
            return Response(
                TinyAnnualReportMediaSerializer(updated_media).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        MediaService.delete_annual_report_media(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class LatestReportMedia(APIView):
    """Get latest report's media"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings.LOGGER.info(f"{request.user} is getting latest report's media")

        try:
            latest = AnnualReport.objects.order_by("-year").first()
            medias = AnnualReportMedia.objects.filter(report=latest).all()
            serializer = TinyAnnualReportMediaSerializer(medias, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        except AnnualReportMedia.DoesNotExist:
            raise NotFound
        except Exception as e:
            settings.LOGGER.error(f"{e}")
            raise e


class AnnualReportMediaUpload(APIView):
    """Upload or update annual report media"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            medias = AnnualReportMedia.objects.filter(report=pk).all()
            serializer = TinyAnnualReportMediaSerializer(medias, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        except AnnualReportMedia.DoesNotExist:
            raise NotFound
        except Exception as e:
            settings.LOGGER.error(f"{e}")
            raise e

    def post(self, request, pk):
        settings.LOGGER.info(f"{request.user} is posting a report media upload")

        report = get_object_or_404(AnnualReport, pk=pk)
        section = request.data["section"]
        file = request.data["file"]

        image_instance = MediaService.get_annual_report_media_by_report_and_kind(
            pk, section
        )

        if image_instance:
            image_instance.file = file
            image_instance.uploader = request.user
            image_instance.save()
            serializer = AnnualReportMediaSerializer(image_instance)
            return Response(serializer.data, status=HTTP_202_ACCEPTED)
        else:
            new_instance_data = {
                "kind": section,
                "file": file,
                "report": report.pk,
                "uploader": request.user.pk,
            }
            serializer = AnnualReportMediaCreationSerializer(data=new_instance_data)
            if serializer.is_valid():
                updated = serializer.save()
                return Response(
                    AnnualReportMediaSerializer(updated).data, HTTP_201_CREATED
                )
            else:
                settings.LOGGER.error(f"{serializer.errors}")
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class AnnualReportMediaDelete(APIView):
    """Delete annual report media by report and section"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, section):
        settings.LOGGER.info(
            f"{request.user} is deleting annual report media with pk {pk}"
        )
        MediaService.delete_annual_report_media_by_report_and_kind(
            pk, section, request.user
        )
        return Response(status=HTTP_204_NO_CONTENT)
