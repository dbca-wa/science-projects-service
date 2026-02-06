# region IMPORTS ====================================================================================================
from math import ceil
from django.conf import settings
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from ..models import Branch
from ..serializers import BranchSerializer, TinyBranchSerializer
from ..services.agency_service import AgencyService

# endregion  =================================================================================================


class Branches(APIView):
    """List and create branches"""
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

            branches = Branch.objects.filter(
                Q(name__icontains=search_term)
            ).order_by("name")
            
            total_branches = branches.count()
            total_pages = ceil(total_branches / page_size)

            serialized_branches = TinyBranchSerializer(
                branches[start:end], many=True, context={"request": request}
            ).data

            return Response({
                "branches": serialized_branches,
                "total_results": total_branches,
                "total_pages": total_pages,
            }, status=HTTP_200_OK)
        else:
            branches = Branch.objects.all()
            serializer = TinyBranchSerializer(branches, many=True)
            return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a branch")
        serializer = BranchSerializer(data=request.data)
        
        if serializer.is_valid():
            branch = serializer.save()
            return Response(
                TinyBranchSerializer(branch).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class BranchDetail(APIView):
    """Retrieve, update, and delete branch"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        branch = AgencyService.get_branch(pk)
        serializer = BranchSerializer(branch)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        branch = AgencyService.get_branch(pk)
        settings.LOGGER.info(f"{request.user} is updating branch detail {branch}")
        
        serializer = BranchSerializer(
            branch,
            data=request.data,
            partial=True,
        )
        
        if serializer.is_valid():
            updated_branch = serializer.save()
            return Response(
                TinyBranchSerializer(updated_branch).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.info(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        branch = AgencyService.get_branch(pk)
        settings.LOGGER.info(f"{request.user} is deleting branch detail {branch}")
        branch.delete()
        return Response(status=HTTP_204_NO_CONTENT)
