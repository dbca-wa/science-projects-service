# region IMPORTS ==================================================================================================
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from ..models import (
    BusinessAreaPhoto,
    ProjectPhoto,
    ProjectPlanMethodologyPhoto,
    AgencyImage,
)
from ..serializers import (
    BusinessAreaPhotoSerializer,
    ProjectPhotoSerializer,
    MethodologyImageCreateSerializer,
    MethodologyImageSerializer,
    AgencyPhotoSerializer,
    TinyBusinessAreaPhotoSerializer,
    TinyProjectPhotoSerializer,
    TinyMethodologyImageSerializer,
    TinyAgencyPhotoSerializer,
)
from ..services.media_service import MediaService

# endregion ========================================================================================================


class BusinessAreaPhotos(APIView):
    """List and create business area photos"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        photos = MediaService.list_business_area_photos()
        serializer = TinyBusinessAreaPhotoSerializer(
            photos, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a business area photo")
        serializer = BusinessAreaPhotoSerializer(data=request.data)
        
        if serializer.is_valid():
            photo = serializer.save()
            return Response(
                TinyBusinessAreaPhotoSerializer(photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class BusinessAreaPhotoDetail(APIView):
    """Retrieve, update, and delete business area photo"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        photo = MediaService.get_business_area_photo(pk)
        serializer = BusinessAreaPhotoSerializer(photo, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        photo = MediaService.get_business_area_photo(pk)
        settings.LOGGER.info(f"{request.user} is updating business area photo {photo}")
        
        if not (photo.uploader == request.user or request.user.is_superuser):
            settings.LOGGER.warning(
                f"{request.user} doesn't have permission to update {photo}"
            )
            raise PermissionDenied
        
        serializer = BusinessAreaPhotoSerializer(photo, data=request.data, partial=True)
        if serializer.is_valid():
            updated_photo = serializer.save()
            return Response(
                TinyBusinessAreaPhotoSerializer(updated_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        photo = MediaService.get_business_area_photo(pk)
        
        if not (photo.uploader == request.user or request.user.is_superuser):
            settings.LOGGER.warning(
                f"{request.user} doesn't have permission to delete {photo}"
            )
            raise PermissionDenied
        
        MediaService.delete_business_area_photo(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class ProjectPhotos(APIView):
    """List and create project photos"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        photos = MediaService.list_project_photos()
        serializer = TinyProjectPhotoSerializer(
            photos, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a project photo")
        serializer = ProjectPhotoSerializer(data=request.data)
        
        if serializer.is_valid():
            photo = serializer.save()
            return Response(
                TinyProjectPhotoSerializer(photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.info(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class ProjectPhotoDetail(APIView):
    """Retrieve, update, and delete project photo"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        photo = MediaService.get_project_photo(pk)
        serializer = ProjectPhotoSerializer(photo, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        photo = MediaService.get_project_photo(pk)
        settings.LOGGER.info(f"{request.user} is updating project photo {photo}")
        
        if not (photo.uploader == request.user or request.user.is_superuser):
            settings.LOGGER.warning(
                f"{request.user} is not allowed to update project photo {photo}"
            )
            raise PermissionDenied
        
        serializer = ProjectPhotoSerializer(photo, data=request.data, partial=True)
        if serializer.is_valid():
            updated_photo = serializer.save()
            return Response(
                TinyProjectPhotoSerializer(updated_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        photo = MediaService.get_project_photo(pk)
        
        if not (photo.uploader == request.user or request.user.is_superuser):
            settings.LOGGER.warning(
                f"{request.user} is not allowed to delete project photo {photo}"
            )
            raise PermissionDenied
        
        MediaService.delete_project_photo(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class MethodologyPhotos(APIView):
    """List and create methodology photos"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        photos = MediaService.list_methodology_photos()
        serializer = TinyMethodologyImageSerializer(
            photos, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is uploading a new methodology photo")
        
        project_plan = request.data["pk"]
        file = request.data["file"]
        data = {
            "project_plan": int(project_plan),
            "file": file,
            "uploader": request.user.pk,
        }
        
        serializer = MethodologyImageCreateSerializer(data=data)
        if serializer.is_valid():
            photo = serializer.save()
            return Response(
                TinyMethodologyImageSerializer(photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.info(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class MethodologyPhotoDetail(APIView):
    """Retrieve, update, and delete methodology photo"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        photo = MediaService.get_methodology_photo_by_project_plan(pk)
        serializer = MethodologyImageSerializer(photo, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        photo = MediaService.get_methodology_photo_by_project_plan(pk)
        settings.LOGGER.info(f"{request.user} is updating methodology photo {photo}")
        
        if not (photo.uploader == request.user or request.user.is_superuser):
            settings.LOGGER.warning(
                f"{request.user} is not allowed to update methodology photo {photo}"
            )
            raise PermissionDenied
        
        serializer = MethodologyImageSerializer(photo, data=request.data, partial=True)
        if serializer.is_valid():
            updated_photo = serializer.save()
            return Response(
                TinyMethodologyImageSerializer(updated_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        photo = MediaService.get_methodology_photo_by_project_plan(pk)
        
        if not (photo.uploader == request.user or request.user.is_superuser):
            settings.LOGGER.warning(
                f"{request.user} is not allowed to delete project photo {photo}"
            )
            raise PermissionDenied
        
        MediaService.delete_methodology_photo(photo.pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class AgencyPhotos(APIView):
    """List and create agency photos"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        photos = MediaService.list_agency_photos()
        serializer = TinyAgencyPhotoSerializer(
            photos, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting an agency photo")
        serializer = AgencyPhotoSerializer(data=request.data)
        
        if serializer.is_valid():
            photo = serializer.save(image=request.data["image"])
            return Response(
                TinyAgencyPhotoSerializer(photo).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class AgencyPhotoDetail(APIView):
    """Retrieve, update, and delete agency photo"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        photo = MediaService.get_agency_photo(pk)
        serializer = AgencyPhotoSerializer(photo, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        photo = MediaService.get_agency_photo(pk)
        settings.LOGGER.info(f"{request.user} is updating agency photo {photo}")
        
        if not request.user.is_superuser:
            settings.LOGGER.warning(
                f"{request.user} cannot update {photo} as they are not a superuser"
            )
            raise PermissionDenied
        
        serializer = AgencyPhotoSerializer(photo, data=request.data, partial=True)
        if serializer.is_valid():
            updated_photo = serializer.save()
            return Response(
                TinyAgencyPhotoSerializer(updated_photo).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            photo = MediaService.get_agency_photo(pk)
            settings.LOGGER.warning(
                f"{request.user} cannot delete {photo} as they are not a superuser"
            )
            raise PermissionDenied
        
        MediaService.delete_agency_photo(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
