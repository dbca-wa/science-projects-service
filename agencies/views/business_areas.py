# region IMPORTS ====================================================================================================
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.views import APIView

from documents.models import ProjectDocument
from documents.serializers import ProjectDocumentSerializer
from medias.models import BusinessAreaPhoto
from projects.models import Project, ProjectMember
from projects.serializers import ProblematicProjectSerializer

from ..models import BusinessArea
from ..serializers import BusinessAreaSerializer, TinyBusinessAreaSerializer
from ..services.agency_service import AgencyService

# endregion  =================================================================================================


class BusinessAreas(APIView):
    """List and create business areas"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_areas = AgencyService.list_business_areas()
        serializer = TinyBusinessAreaSerializer(business_areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def handle_ba_image(self, image):
        """Handle business area image upload"""
        if isinstance(image, str):
            return image
        elif image is not None:
            original_filename = image.name
            subfolder = "business_areas"
            file_path = f"{subfolder}/{original_filename}"

            if default_storage.exists(file_path):
                full_file_path = default_storage.path(file_path)
                if os.path.exists(full_file_path):
                    existing_file_size = os.path.getsize(full_file_path)
                    new_file_size = image.size
                    if existing_file_size == new_file_size:
                        return file_path

            content = ContentFile(image.read())
            file_path = default_storage.save(file_path, content)
            return file_path

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a business area")

        image = request.data.get("image")
        if image:
            if isinstance(image, str) and (
                image.startswith("http://") or image.startswith("https://")
            ):
                if not image.lower().endswith((".jpg", ".jpeg", ".png")):
                    return Response(
                        "The URL is not a valid photo file", status=HTTP_400_BAD_REQUEST
                    )

        division_id = request.data.get("division")
        ba_data = {
            "agency": request.data.get("agency"),
            "name": request.data.get("name"),
            "focus": request.data.get("focus"),
            "introduction": request.data.get("introduction"),
            "data_custodian": request.data.get("data_custodian"),
            "finance_admin": request.data.get("finance_admin"),
            "leader": request.data.get("leader"),
        }

        if division_id and division_id is not None:
            ba_data["division"] = int(division_id)

        serializer = BusinessAreaSerializer(data=ba_data)

        if serializer.is_valid():
            with transaction.atomic():
                new_business_area = serializer.save()

                try:
                    image_data = {
                        "file": self.handle_ba_image(image) if image else None,
                        "uploader": request.user,
                        "business_area": new_business_area,
                    }
                except ValueError as e:
                    settings.LOGGER.error(f"Error on handling BA image: {e}")
                    return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)

                try:
                    BusinessAreaPhoto.objects.create(**image_data)
                except Exception as e:
                    settings.LOGGER.error(
                        f"Error on creating new BA Photo instance: {e}"
                    )
                    new_business_area.delete()
                    return Response(
                        {"error": str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR
                    )

                optimized_ba = BusinessArea.objects.select_related(
                    "division", "image"
                ).get(pk=new_business_area.pk)

                return Response(
                    TinyBusinessAreaSerializer(optimized_ba).data,
                    status=HTTP_201_CREATED,
                )
        else:
            settings.LOGGER.error(f"BA Serializer invalid: {serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class BusinessAreaDetail(APIView):
    """Retrieve, update, and delete business area"""

    permission_classes = [IsAuthenticated]

    def handle_ba_image(self, image):
        """Handle business area image upload"""
        if isinstance(image, str):
            return image
        elif image is not None:
            original_filename = image.name
            subfolder = "business_areas"
            file_path = f"{subfolder}/{original_filename}"

            if default_storage.exists(file_path):
                full_file_path = default_storage.path(file_path)
                if os.path.exists(full_file_path):
                    existing_file_size = os.path.getsize(full_file_path)
                    new_file_size = image.size
                    if existing_file_size == new_file_size:
                        return file_path

            content = ContentFile(image.read())
            file_path = default_storage.save(file_path, content)
            return file_path

    def get(self, request, pk):
        ba = AgencyService.get_business_area(pk)
        serializer = BusinessAreaSerializer(ba)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        ba = AgencyService.get_business_area(pk)
        settings.LOGGER.info(f"{request.user} is updating business area {ba}")

        image = request.data.get("image")
        if image:
            if isinstance(image, str) and (
                image.startswith("http://") or image.startswith("https://")
            ):
                if not image.lower().endswith((".jpg", ".jpeg", ".png")):
                    return Response(
                        "The URL is not a valid photo file", status=HTTP_400_BAD_REQUEST
                    )
        else:
            selected_image_url = request.data.get("selectedImageUrl")
            if selected_image_url == "delete":
                photo = BusinessAreaPhoto.objects.filter(business_area=pk).first()
                if photo:
                    photo.delete()

        division_id = request.data.get("division")
        leader = request.data.get("leader")
        if leader == "0" or leader == 0:
            leader = None

        ba_data = {
            key: value
            for key, value in {
                "name": request.data.get("name"),
                "slug": request.data.get("slug"),
                "agency": request.data.get("agency"),
                "focus": request.data.get("focus"),
                "introduction": request.data.get("introduction"),
                "data_custodian": request.data.get("data_custodian"),
                "finance_admin": request.data.get("finance_admin"),
                "leader": leader,
            }.items()
            if value is not None or key == "leader"
        }

        if division_id is not None:
            try:
                ba_data["division"] = int(division_id)
            except (ValueError, TypeError):
                pass

        serializer = BusinessAreaSerializer(ba, data=ba_data, partial=True)

        if serializer.is_valid():
            with transaction.atomic():
                uba = serializer.save()

                if image:
                    try:
                        currentphoto = BusinessAreaPhoto.objects.get(business_area=pk)
                    except BusinessAreaPhoto.DoesNotExist:
                        image_data = {
                            "file": self.handle_ba_image(image),
                            "uploader": request.user,
                            "business_area": uba,
                        }
                        BusinessAreaPhoto.objects.create(**image_data)
                    else:
                        currentphoto.file = self.handle_ba_image(image)
                        currentphoto.save()

                return Response(
                    TinyBusinessAreaSerializer(uba).data,
                    status=HTTP_202_ACCEPTED,
                )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ba = AgencyService.get_business_area(pk)
        settings.LOGGER.info(f"{request.user} is deleting business area {ba}")
        ba.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class MyBusinessAreas(APIView):
    """Get business areas led by current user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_areas = BusinessArea.objects.filter(leader=request.user.pk)
        serializer = TinyBusinessAreaSerializer(business_areas, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class BusinessAreasUnapprovedDocs(APIView):
    """Get unapproved documents for business areas"""

    def get_unapproved_docs_for_ba(self, pk):
        try:
            docs = ProjectDocument.objects.filter(
                project__business_area=pk, project_lead_approval_granted=False
            ).distinct()
        except ProjectDocument.DoesNotExist:
            raise NotFound
        except Exception as e:
            settings.LOGGER.error(f"Error: {e}")
            docs = ProjectDocument.objects.none()
        return docs

    def post(self, request):
        try:
            pks_array = request.data.get("baArray")
            settings.LOGGER.info(
                f"{request.user} is Getting My BA Unapproved Docs: {pks_array}"
            )

            data = {}
            for ba_pk in pks_array:
                unapproved = self.get_unapproved_docs_for_ba(ba_pk)
                processed_unapproved = []
                seen_ids = set()
                unlinked_docs = []

                for item in unapproved:
                    if item.pk not in seen_ids:
                        if item.has_project_document_data() is False:
                            unlinked_docs.append(item)
                        else:
                            processed_unapproved.append(item)
                            seen_ids.add(item.pk)

                serializer = ProjectDocumentSerializer(processed_unapproved, many=True)
                serializer2 = ProjectDocumentSerializer(unlinked_docs, many=True)

                data[ba_pk] = {
                    "linked": serializer.data,
                    "unlinked": serializer2.data,
                }

                if data[ba_pk]["linked"]:
                    ba_name = data[ba_pk]["linked"][0]["project"]["business_area"][
                        "name"
                    ]
                    settings.LOGGER.warning(
                        f"Unapproved Doc Count for BA '{ba_name}' ({ba_pk}): "
                        f"{len(processed_unapproved)}\nUnlinked Doc Count for BA {len(unlinked_docs)}"
                    )
                else:
                    settings.LOGGER.warning(
                        f"Unapproved Doc Count for BA {ba_pk}: {len(processed_unapproved)}\n"
                        f"Unlinked Doc Count for BA: {len(unlinked_docs)}"
                    )

            return Response(data=data, status=HTTP_200_OK)
        except Exception as e:
            settings.LOGGER.error(f"{e}")
            return Response({"msg": e}, HTTP_400_BAD_REQUEST)


class BusinessAreasProblematicProjects(APIView):
    """Get problematic projects for business areas"""

    def get_projects_in_ba_array(self, ba_array):
        try:
            projects = (
                Project.objects.filter(business_area__in=ba_array)
                .select_related("business_area", "image")
                .prefetch_related("members", "members__user")
            )
        except Project.DoesNotExist:
            raise NotFound
        except Exception:
            return Project.objects.none()
        return projects

    def get(self, request):
        try:
            business_area_id = request.query_params.get("business_area_id")
            if not business_area_id:
                return Response(
                    {"error": "business_area_id parameter is required"},
                    status=HTTP_400_BAD_REQUEST,
                )

            settings.LOGGER.info(
                f"{request.user} is Getting Problematic Projects for Business Area {business_area_id}"
            )

            all_projects = self.get_projects_in_ba_array([business_area_id])
            memberless_projects = []
            no_leader_tag_projects = []
            multiple_leader_tag_projects = []
            externally_led_projects = []

            for p in all_projects:
                members = p.members.all()
                leader_tag_count = 0
                external_leader = False

                for mem in members:
                    if mem.role == ProjectMember.RoleChoices.SUPERVISING:
                        leader_tag_count += 1
                    if mem.is_leader is True and mem.user.is_staff is False:
                        external_leader = True

                if len(members) < 1:
                    memberless_projects.append(p)
                else:
                    if external_leader:
                        externally_led_projects.append(p)
                    if leader_tag_count == 0:
                        no_leader_tag_projects.append(p)
                    elif leader_tag_count > 1:
                        multiple_leader_tag_projects.append(p)

            data = {
                "no_members": ProblematicProjectSerializer(
                    memberless_projects, many=True
                ).data,
                "no_leader": ProblematicProjectSerializer(
                    no_leader_tag_projects, many=True
                ).data,
                "external_leader": ProblematicProjectSerializer(
                    externally_led_projects, many=True
                ).data,
                "multiple_leads": ProblematicProjectSerializer(
                    multiple_leader_tag_projects, many=True
                ).data,
            }

            return Response(data=data, status=HTTP_200_OK)

        except Exception as e:
            settings.LOGGER.error(f"{e}")
            return Response({"msg": str(e)}, status=HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            pks_array = request.data.get("baArray")
            settings.LOGGER.info(
                f"{request.user} is Getting My BA Problem Projects: {pks_array}"
            )
            data = {}

            for ba_pk in pks_array:
                projects_in_ba = Project.objects.filter(
                    business_area=ba_pk
                ).prefetch_related("members", "members__user")

                memberless_projects = []
                no_leader_tag_projects = []
                multiple_leader_tag_projects = []
                externally_led_projects = []

                for p in projects_in_ba:
                    members = p.members.all()
                    leader_tag_count = 0
                    external_leader = False

                    for mem in members:
                        if mem.role == ProjectMember.RoleChoices.SUPERVISING:
                            leader_tag_count += 1
                        if mem.is_leader is True and mem.user.is_staff is False:
                            external_leader = True

                    if len(members) < 1:
                        memberless_projects.append(p)
                    else:
                        if external_leader:
                            externally_led_projects.append(p)
                        if leader_tag_count == 0:
                            no_leader_tag_projects.append(p)
                        elif leader_tag_count > 1:
                            multiple_leader_tag_projects.append(p)

                data[ba_pk] = {
                    "no_members": ProblematicProjectSerializer(
                        memberless_projects, many=True
                    ).data,
                    "no_leader": ProblematicProjectSerializer(
                        no_leader_tag_projects, many=True
                    ).data,
                    "external_leader": ProblematicProjectSerializer(
                        externally_led_projects, many=True
                    ).data,
                    "multiple_leads": ProblematicProjectSerializer(
                        multiple_leader_tag_projects, many=True
                    ).data,
                }

            return Response(data=data, status=HTTP_200_OK)

        except Exception as e:
            settings.LOGGER.error(f"{e}")
            return Response({"msg": e}, HTTP_400_BAD_REQUEST)


class SetBusinessAreaActive(APIView):
    """Toggle business area active status"""

    def post(self, request, pk):
        ba = AgencyService.get_business_area(pk)
        settings.LOGGER.info(f"{request.user} is changing active status of {ba}")

        try:
            updated_ba = AgencyService.set_business_area_active(pk)
            serializer = BusinessAreaSerializer(updated_ba)
            return Response(serializer.data, HTTP_202_ACCEPTED)
        except Exception as e:
            settings.LOGGER.error(f"Error setting active status of Business Area: {e}")
            return Response({"error": str(e)}, HTTP_400_BAD_REQUEST)
