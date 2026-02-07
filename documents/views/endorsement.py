"""
Endorsement views
"""

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from medias.models import AECEndorsementPDF
from medias.serializers import AECPDFCreateSerializer
from projects.models import Project

from ..models import Endorsement, ProjectPlan
from ..serializers import (
    EndorsementCreateSerializer,
    EndorsementSerializer,
    MiniEndorsementSerializer,
    TinyEndorsementSerializer,
)


class Endorsements(APIView):
    """List and create endorsements"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all endorsements"""
        all_endorsements = Endorsement.objects.all()
        serializer = TinyEndorsementSerializer(
            all_endorsements,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create a new endorsement"""
        settings.LOGGER.info(f"{request.user} is posting an endorsement")
        serializer = EndorsementCreateSerializer(data=request.data)

        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        new_endorsement = serializer.save()
        return Response(
            TinyEndorsementSerializer(new_endorsement).data,
            status=HTTP_201_CREATED,
        )


class EndorsementDetail(APIView):
    """Get and update endorsements"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get endorsement by ID"""
        try:
            endorsement = Endorsement.objects.get(pk=pk)
        except Endorsement.DoesNotExist:
            raise NotFound

        serializer = EndorsementSerializer(
            endorsement,
            context={"request": request},
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update endorsement"""
        settings.LOGGER.info(f"{request.user} is updating endorsement for {pk}")

        try:
            endorsement = Endorsement.objects.get(pk=pk)
        except Endorsement.DoesNotExist:
            raise NotFound

        serializer = EndorsementSerializer(
            endorsement,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        updated_endorsement = serializer.save()
        return Response(
            TinyEndorsementSerializer(updated_endorsement).data,
            status=HTTP_202_ACCEPTED,
        )


class EndorsementsPendingMyAction(APIView):
    """Get endorsements pending user's action"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get endorsements requiring action from current user"""
        settings.LOGGER.info(f"{request.user} is getting endorsements pending action")

        is_aec = request.user.is_aec
        is_superuser = request.user.is_superuser

        aec_input_required = []

        # Build query for AEC endorsements
        q_ae = Q(ae_endorsement_required=True, ae_endorsement_provided=False) & (
            Q(ae_endorsement_required=True) if is_aec or is_superuser else Q()
        )

        # Filter endorsements based on conditions
        filtered_endorsements = Endorsement.objects.filter(
            q_ae,
            project_plan__project__status__in=Project.ACTIVE_ONLY,
        )

        for endorsement in filtered_endorsements:
            if (
                endorsement.ae_endorsement_required
                and not endorsement.ae_endorsement_provided
            ):
                aec_input_required.append(endorsement)

        all_aec = MiniEndorsementSerializer(
            aec_input_required if aec_input_required else [],
            many=True,
            context={"request": request},
        ).data

        data = {
            "aec": all_aec,
        }

        return Response(data, status=HTTP_200_OK)


class SeekEndorsement(APIView):
    """Seek endorsement for a project plan"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Request endorsement for project plan"""
        try:
            project_plan = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound

        endorsement = Endorsement.objects.filter(project_plan=project_plan).first()

        if not endorsement:
            raise NotFound("Endorsement not found for this project plan")

        settings.LOGGER.info(
            f"{request.user} is seeking an endorsement for project plan {project_plan} "
            f"with db object {endorsement}"
        )

        end_serializer = EndorsementSerializer(
            endorsement,
            data=request.data,
            partial=True,
        )

        if not end_serializer.is_valid():
            settings.LOGGER.error(
                f"Endorsement serializer invalid: {end_serializer.errors}"
            )
            return Response(end_serializer.errors, status=HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            updated = end_serializer.save()

            # Handle PDF file upload
            pdf_file = request.FILES.get("aec_pdf_file")

            if pdf_file:
                existing_pdf = AECEndorsementPDF.objects.filter(
                    endorsement=updated
                ).first()

                if existing_pdf:
                    # Update existing PDF
                    existing_pdf.file = pdf_file
                    existing_pdf.save()
                    settings.LOGGER.info("Found entry and updated PDF")
                else:
                    # Create new PDF
                    new_instance_data = {
                        "file": pdf_file,
                        "endorsement": updated.id,
                        "creator": request.user.id,
                    }
                    new_instance_serializer = AECPDFCreateSerializer(
                        data=new_instance_data
                    )

                    if not new_instance_serializer.is_valid():
                        settings.LOGGER.error(f"{new_instance_serializer.errors}")
                        return Response(
                            new_instance_serializer.errors, status=HTTP_400_BAD_REQUEST
                        )

                    new_instance_serializer.save()
                    settings.LOGGER.info("Saved new valid pdf instance")

            updated_ser_data = EndorsementSerializer(updated).data
            return Response(updated_ser_data, status=HTTP_202_ACCEPTED)


class DeleteAECEndorsement(APIView):
    """Delete AEC endorsement and associated PDF"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Delete AEC endorsement for project plan"""
        try:
            project_plan = ProjectPlan.objects.get(pk=pk)
        except ProjectPlan.DoesNotExist:
            raise NotFound

        endorsement = Endorsement.objects.filter(project_plan=project_plan).first()

        if not endorsement:
            raise NotFound("Endorsement not found for this project plan")

        settings.LOGGER.info(
            f"{request.user} is deleting aec endorsement and pdf for project plan "
            f"{project_plan} with db object {endorsement}"
        )

        # Update endorsement to remove approval
        end_serializer = EndorsementSerializer(
            endorsement,
            data={"ae_endorsement_provided": False},
            partial=True,
        )

        if not end_serializer.is_valid():
            settings.LOGGER.error(
                f"Endorsement serializer invalid: {end_serializer.errors}"
            )
            return Response(end_serializer.errors, status=HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Update endorsement
            updated = end_serializer.save()

            # Delete associated PDF
            pdf_obj = AECEndorsementPDF.objects.filter(endorsement=endorsement).first()
            if pdf_obj:
                pdf_obj.delete()

            updated_ser_data = EndorsementSerializer(updated).data
            return Response(updated_ser_data, status=HTTP_202_ACCEPTED)
