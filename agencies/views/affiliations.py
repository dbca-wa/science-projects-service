# region IMPORTS ====================================================================================================
from math import ceil

from django.conf import settings
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.views import APIView

from users.models import UserWork
from users.serializers import UserWorkAffiliationUpdateSerializer

from ..models import Affiliation
from ..serializers import AffiliationSerializer
from ..services.agency_service import AgencyService

# endregion  =================================================================================================


class Affiliations(APIView):
    """List and create affiliations"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_term = request.query_params.get("searchTerm")

        if search_term:
            try:
                page = int(request.query_params.get("page", 1))
            except ValueError:
                page = 1

            page_size = settings.PAGE_SIZE
            start = (page - 1) * page_size
            end = start + page_size

            affiliations = Affiliation.objects.filter(
                Q(name__icontains=search_term)
            ).order_by("name")

            total_affiliations = affiliations.count()
            total_pages = ceil(total_affiliations / page_size)

            serialized_affiliations = AffiliationSerializer(
                affiliations[start:end], many=True, context={"request": request}
            ).data

            return Response(
                {
                    "affiliations": serialized_affiliations,
                    "total_results": total_affiliations,
                    "total_pages": total_pages,
                },
                status=HTTP_200_OK,
            )
        else:
            affiliations = Affiliation.objects.all()
            serializer = AffiliationSerializer(affiliations, many=True)
            return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting an affiliation")
        serializer = AffiliationSerializer(data=request.data)

        if serializer.is_valid():
            affiliation = serializer.save()
            return Response(
                AffiliationSerializer(affiliation).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class AffiliationDetail(APIView):
    """Retrieve, update, and delete affiliation"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if pk == 0:
            return Response(status=HTTP_200_OK)

        affiliation = AgencyService.get_affiliation(pk)
        serializer = AffiliationSerializer(affiliation)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        affiliation = AgencyService.get_affiliation(pk)
        settings.LOGGER.info(f"{request.user} is updating affiliation {affiliation}")

        serializer = AffiliationSerializer(
            affiliation,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            updated_affiliation = serializer.save()
            return Response(
                AffiliationSerializer(updated_affiliation).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.info(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        affiliation = AgencyService.get_affiliation(pk)
        settings.LOGGER.info(f"{request.user} is deleting affiliation {affiliation}")

        result = AgencyService.delete_affiliation(pk, request.user)

        return Response(result, status=HTTP_200_OK)


class AffiliationsMerge(APIView):
    """Merge multiple affiliations into one"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is merging affiliations")

        primary_affiliation = request.data.get("primaryAffiliation")
        secondary_affiliations = request.data.get("secondaryAffiliations")

        if not isinstance(secondary_affiliations, list):
            secondary_affiliations = [secondary_affiliations]

        for item in secondary_affiliations:
            try:
                instances_to_update = UserWork.objects.filter(
                    affiliation=item["pk"]
                ).all()

                for ins in instances_to_update:
                    serializer = UserWorkAffiliationUpdateSerializer(
                        instance=ins,
                        data={"affiliation": primary_affiliation["pk"]},
                        partial=True,
                    )
                    if serializer.is_valid():
                        serializer.save()

            except UserWork.DoesNotExist:
                pass
            except Exception as e:
                settings.LOGGER.error(
                    f"{instances_to_update} could not be updated...{e}"
                )
                return Response(
                    {"message": f"Error! {e}"},
                    status=HTTP_400_BAD_REQUEST,
                )
            finally:
                if item["pk"] != primary_affiliation["pk"]:
                    instance_to_delete = Affiliation.objects.get(pk=item["pk"])
                    settings.LOGGER.info(
                        f"{instance_to_delete.name} is being deleted..."
                    )
                    instance_to_delete.delete()

        settings.LOGGER.info("Merged!")
        return Response({"message": "Merged!"}, status=HTTP_202_ACCEPTED)


class AffiliationsCleanOrphaned(APIView):
    """Clean orphaned affiliations with no references"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is cleaning orphaned affiliations")

        try:
            result = AgencyService.clean_orphaned_affiliations(request.user)
            return Response(result, status=HTTP_200_OK)
        except Exception as e:
            settings.LOGGER.error(
                f"Error during orphaned affiliation cleanup: {str(e)}"
            )
            return Response(
                {"message": f"Error during cleanup: {str(e)}"},
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )
