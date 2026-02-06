# region IMPORTS ==================================================================================================
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
)

from ..models import ProjectDocumentPDF
from ..serializers import (
    ProjectDocumentPDFSerializer,
    ProjectDocumentPDFCreationSerializer,
    TinyAnnualReportMediaSerializer,
)
from ..services.media_service import MediaService

# endregion ========================================================================================================


class ProjectDocPDFS(APIView):
    """List and create project document PDFs"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pdfs = MediaService.list_project_document_pdfs()
        serializer = ProjectDocumentPDFSerializer(
            pdfs,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a project document pdf")
        serializer = ProjectDocumentPDFCreationSerializer(data=request.data)
        
        if serializer.is_valid():
            pdf = serializer.save()
            return Response(
                ProjectDocumentPDFSerializer(pdf).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)
