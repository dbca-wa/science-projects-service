# region IMPORTS ====================================================================================================

import os
from math import ceil
from pprint import pprint
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.conf import settings
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    NotFound,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

# Project imports ------------------------------

from documents.models import ProjectDocument
from documents.serializers import ProjectDocumentSerializer
from projects.models import Project, ProjectMember
from projects.serializers import (
    ProblematicProjectSerializer,
)
from medias.models import BusinessAreaPhoto
from users.models import User, UserWork
from users.serializers import (
    UserWorkAffiliationUpdateSerializer,
)
from .models import (
    Branch,
    BusinessArea,
    DepartmentalService,
    Agency,
    Affiliation,
    Division,
)
from .serializers import (
    AffiliationSerializer,
    BranchSerializer,
    AgencySerializer,
    DepartmentalServiceSerializer,
    DivisionSerializer,
    TinyBranchSerializer,
    TinyBusinessAreaSerializer,
    BusinessAreaSerializer,
    TinyDepartmentalServiceSerializer,
    TinyAgencySerializer,
    TinyDivisionSerializer,
)

# endregion  =================================================================================================


# region Affiliation Views ====================================================================================================


class Affiliations(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        try:
            page = int(req.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = settings.PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size

        search_term = req.query_params.get("searchTerm")

        if search_term:
            # Apply filtering based on the search term
            affiliations = Affiliation.objects.filter(Q(name__icontains=search_term))
            # Sort branches alphabetically based on email
            affiliations = affiliations.order_by("name")
            total_affiliations = affiliations.count()
            total_pages = ceil(total_affiliations / page_size)

            serialized_affiliations = AffiliationSerializer(
                affiliations[start:end], many=True, context={"request": req}
            ).data

            response_data = {
                "affiliations": serialized_affiliations,
                "total_results": total_affiliations,
                "total_pages": total_pages,
            }
            return Response(response_data, status=HTTP_200_OK)

        else:
            all = Affiliation.objects.all()
            ser = AffiliationSerializer(
                all,
                many=True,
            )
            return Response(
                ser.data,
                status=HTTP_200_OK,
            )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting an affiliation")
        ser = AffiliationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            affiliation = ser.save()
            return Response(
                AffiliationSerializer(affiliation).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AffiliationDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Affiliation.objects.get(pk=pk)
        except Affiliation.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        if pk == 0:
            return Response(
                status=HTTP_200_OK,
            )
        affiliation = self.go(pk)
        ser = AffiliationSerializer(affiliation)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        affiliation = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting affiliation {affiliation}")
        affiliation.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        affiliation = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating affiliation {affiliation}")
        ser = AffiliationSerializer(
            affiliation,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_affiliation = ser.save()
            return Response(
                AffiliationSerializer(u_affiliation).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.info(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AffiliationsMerge(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is merging affiliations")
        primaryAffiliation = req.data.get("primaryAffiliation")
        secondaryAffiliations = req.data.get("secondaryAffiliations")
        if not isinstance(secondaryAffiliations, list):
            secondaryAffiliations = [secondaryAffiliations]

        # Merge logic -----------------------
        for item in secondaryAffiliations:
            try:
                instances_to_update = UserWork.objects.filter(
                    affiliation=item["pk"]
                ).all()
                for ins in instances_to_update:
                    ser = UserWorkAffiliationUpdateSerializer(
                        instance=ins,
                        data={
                            "affiliation": primaryAffiliation["pk"],
                        },
                        partial=True,
                    )
                    if ser.is_valid():
                        updated = ser.save()

            except UserWork.DoesNotExist:
                # If nothing exists that uses the affiliation just go to next step and delete
                pass
            except Exception as e:
                settings.LOGGER.error(
                    msg=f"{instances_to_update} could not be updated...{e}"
                )
                return Response(
                    {"message": f"Error! {e}"},
                    status=HTTP_400_BAD_REQUEST,
                )
            finally:
                # Delete old one
                if item["pk"] != primaryAffiliation["pk"]:
                    instance_to_delete = Affiliation.objects.get(pk=item["pk"])
                    settings.LOGGER.info(
                        msg=f"{instance_to_delete.name} is being deleted..."
                    )
                    instance_to_delete.delete()

        settings.LOGGER.info(msg=f"Merged!")
        return Response(
            {"message": "Merged!"},
            status=HTTP_202_ACCEPTED,
        )


# endregion  =================================================================================================


# region Agency Views ====================================================================================================


class Agencies(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = Agency.objects.all()
        ser = TinyAgencySerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting an agency")
        ser = AgencySerializer(
            data=req.data,
        )
        if ser.is_valid():
            Agency = ser.save()
            return Response(
                TinyAgencySerializer(Agency).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AgencyDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Agency.objects.get(pk=pk)
        except Agency.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        Agency = self.go(pk)
        ser = AgencySerializer(Agency)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        Agency = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting agency {Agency}")
        Agency.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        Agency = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating {Agency}")
        ser = AgencySerializer(
            Agency,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_Agency = ser.save()
            return Response(
                TinyAgencySerializer(updated_Agency).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================


# region Branch Views ====================================================================================================


class Branches(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        try:
            page = int(req.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = settings.PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size

        search_term = req.query_params.get("searchTerm")

        if search_term:
            # Apply filtering based on the search term
            branches = Branch.objects.filter(Q(name__icontains=search_term))
            # Sort branches alphabetically based on email
            branches = branches.order_by("name")
            total_branches = branches.count()
            total_pages = ceil(total_branches / page_size)

            serialized_branches = TinyBranchSerializer(
                branches[start:end], many=True, context={"request": req}
            ).data

            response_data = {
                "branches": serialized_branches,
                "total_results": total_branches,
                "total_pages": total_pages,
            }
            return Response(response_data, status=HTTP_200_OK)

        else:
            branches = Branch.objects.all()
            ser = TinyBranchSerializer(branches, many=True)
            return Response(ser.data, status=HTTP_200_OK)

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a branch")
        ser = BranchSerializer(
            data=req.data,
        )
        if ser.is_valid():
            branch = ser.save()
            return Response(
                TinyBranchSerializer(branch).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class BranchDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        branch = self.go(pk)
        ser = BranchSerializer(branch)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        branch = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting branch detail {branch}")
        branch.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        branch = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating branch detail {branch}")
        ser = BranchSerializer(
            branch,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_branch = ser.save()
            return Response(
                TinyBranchSerializer(updated_branch).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.info(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================


# region Business Area Views ====================================================================================================


class BusinessAreas(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        # Added select_related and prefetch_related to prevent N+1 queries
        all = (
            BusinessArea.objects.select_related(
                "division",  # For TinyDivisionSerializer
                "image",  # For BusinessAreaImageSerializer (OneToOne)
            )
            .prefetch_related(
                "division__directorate_email_list",  # For division email list queries
            )
            .all()
        )

        ser = TinyBusinessAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def handle_ba_image(self, image):
        if isinstance(image, str):
            return image
        elif image is not None:
            # Get the original file name with extension
            original_filename = image.name

            # Specify the subfolder within your media directory
            subfolder = "business_areas"

            # Combine the subfolder and filename to create the full file path
            file_path = f"{subfolder}/{original_filename}"

            # Check if a file with the same name exists in the subfolder
            if default_storage.exists(file_path):
                # A file with the same name already exists
                full_file_path = default_storage.path(file_path)
                if os.path.exists(full_file_path):
                    existing_file_size = os.path.getsize(full_file_path)
                    new_file_size = (
                        image.size
                    )  # Assuming image.size returns the size of the uploaded file
                    if existing_file_size == new_file_size:
                        # The file with the same name and size already exists, so use the existing file
                        return file_path

            # If the file doesn't exist or has a different size, continue with the file-saving logic
            content = ContentFile(image.read())
            file_path = default_storage.save(file_path, content)
            # `file_path` now contains the path to the saved file
            return file_path

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a business area")
        image = req.data.get("image")
        if image:
            if isinstance(image, str) and (
                image.startswith("http://") or image.startswith("https://")
            ):
                # URL provided, validate the URL
                if not image.lower().endswith((".jpg", ".jpeg", ".png")):
                    error_message = "The URL is not a valid photo file"
                    return Response(error_message, status=HTTP_400_BAD_REQUEST)

        division_id = req.data.get("division")
        if division_id and division_id != None:
            ba_data = {
                # "old_id": req.data.get("old_id"),
                "division": int(division_id),
                "agency": req.data.get("agency"),
                "name": req.data.get("name"),
                "focus": req.data.get("focus"),
                "introduction": req.data.get("introduction"),
                "data_custodian": req.data.get("data_custodian"),
                "finance_admin": req.data.get("finance_admin"),
                "leader": req.data.get("leader"),
            }
        else:
            ba_data = {
                # "old_id": req.data.get("old_id"),
                # "slug": req.data.get("slug"),
                "agency": req.data.get("agency"),
                "name": req.data.get("name"),
                "focus": req.data.get("focus"),
                "introduction": req.data.get("introduction"),
                "data_custodian": req.data.get("data_custodian"),
                "finance_admin": req.data.get("finance_admin"),
                "leader": req.data.get("leader"),
            }

        ser = BusinessAreaSerializer(data=ba_data)

        if ser.is_valid():
            with transaction.atomic():
                # First create the Business Area
                new_business_area = ser.save()

                # Then create the related image based on the ba
                try:
                    image_data = {
                        "file": self.handle_ba_image(image) if image else None,
                        "uploader": req.user,
                        "business_area": new_business_area,
                    }
                except ValueError as e:
                    settings.LOGGER.error(msg=f"Error on handling BA image: {e}")
                    error_message = str(e)
                    response_data = {"error": error_message}
                    return Response(response_data, status=HTTP_400_BAD_REQUEST)

                # Create the image with prepped data
                try:
                    new_bap_instance = BusinessAreaPhoto.objects.create(**image_data)
                    print(image_data)
                    # bap_response = TinyBusinessAreaPhotoSerializer(
                    #     new_bap_instance
                    # ).data
                except Exception as e:
                    settings.LOGGER.error(
                        msg=f"Error on creating new BA Photo instance: {e}"
                    )
                    new_business_area.delete()
                    response_data = {"error": str(e)}
                    return Response(
                        response_data, status=HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # Return optimized response - fetch the new business area with relations
                optimized_ba = BusinessArea.objects.select_related(
                    "division", "image"
                ).get(pk=new_business_area.pk)

                return Response(
                    TinyBusinessAreaSerializer(optimized_ba).data,
                    status=HTTP_201_CREATED,
                )
        else:
            settings.LOGGER.error(msg=f"BA Serializer invalid: {ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class BusinessAreaDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = BusinessArea.objects.get(pk=pk)
        except BusinessArea.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        ba = self.go(pk)
        ser = BusinessAreaSerializer(ba)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        ba = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting business area {ba}")
        ba.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def handle_ba_image(self, image):
        if isinstance(image, str):
            return image
        elif image is not None:
            # Get the original file name with extension
            original_filename = image.name

            # Specify the subfolder within your media directory
            subfolder = "business_areas"

            # Combine the subfolder and filename to create the full file path
            file_path = f"{subfolder}/{original_filename}"

            # Check if a file with the same name exists in the subfolder
            if default_storage.exists(file_path):
                # A file with the same name already exists
                full_file_path = default_storage.path(file_path)
                if os.path.exists(full_file_path):
                    existing_file_size = os.path.getsize(full_file_path)
                    new_file_size = (
                        image.size
                    )  # Assuming image.size returns the size of the uploaded file
                    if existing_file_size == new_file_size:
                        # The file with the same name and size already exists, so use the existing file
                        return file_path

            # If the file doesn't exist or has a different size, continue with the file-saving logic
            content = ContentFile(image.read())
            file_path = default_storage.save(file_path, content)
            # `file_path` now contains the path to the saved file

            return file_path

    def get_ba_photo(self, pk):
        try:
            obj = BusinessAreaPhoto.objects.get(business_area=pk)
        except BusinessAreaPhoto.DoesNotExist:
            raise NotFound
        return obj

    def put(self, req, pk):
        ba = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating business area {ba}")

        image = req.data.get("image")
        print(req.data)

        if image:
            if isinstance(image, str) and (
                image.startswith("http://") or image.startswith("https://")
            ):
                # URL provided, validate the URL
                if not image.lower().endswith((".jpg", ".jpeg", ".png")):
                    error_message = "The URL is not a valid photo file"
                    return Response(error_message, status=HTTP_400_BAD_REQUEST)
        else:
            selectedImageUrl = req.data.get("selectedImageUrl")
            if selectedImageUrl == "delete":
                photo = BusinessAreaPhoto.objects.filter(business_area=pk).first()
                if photo:
                    photo.delete()

        division_id = req.data.get("division")
        print("DIV ID: ", division_id)

        # Pre-process the leader field to set to none if 0 received
        leader = req.data.get("leader")
        if leader == "0" or leader == 0:
            leader = None

        ba_data = {
            key: value
            for key, value in {
                "old_id": req.data.get("old_id"),
                "name": req.data.get("name"),
                "slug": req.data.get("slug"),
                "agency": req.data.get("agency"),
                "focus": req.data.get("focus"),
                "introduction": req.data.get("introduction"),
                "data_custodian": req.data.get("data_custodian"),
                "finance_admin": req.data.get("finance_admin"),
                "leader": leader,
            }.items()
            if value is not None or key == "leader"
            #   and (not isinstance(value, list) or value)
        }

        if division_id is not None:
            try:
                ba_data["division"] = int(division_id)
            except (ValueError, TypeError) as e:
                print(e)
                pass

        ser = BusinessAreaSerializer(
            ba,
            data=ba_data,
            partial=True,
        )

        if ser.is_valid():
            with transaction.atomic():
                # First create or update the Business Area
                uba = ser.save()
                print("updated")
                if image:
                    try:
                        # Check if Photo already present:
                        currentphoto = BusinessAreaPhoto.objects.get(business_area=pk)
                    except BusinessAreaPhoto.DoesNotExist as e:
                        settings.LOGGER.error(msg=f"{e}")
                        # If the image doesn't exist, create it
                        image_data = {
                            "file": self.handle_ba_image(image),
                            "uploader": req.user,
                            "business_area": uba,
                        }
                        currentphoto = BusinessAreaPhoto.objects.create(**image_data)
                    else:
                        # Update the existing photo
                        currentphoto.file = self.handle_ba_image(image)
                        currentphoto.save()

                return Response(
                    TinyBusinessAreaSerializer(uba).data,
                    status=HTTP_202_ACCEPTED,
                )
        else:
            print("\nSerializer invalid\n")
            pprint(ser.data)
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class MyBusinessAreas(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = BusinessArea.objects.filter(leader=req.user.pk)
        ser = TinyBusinessAreaSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class BusinessAreasUnapprovedDocs(APIView):
    def get_unapproved_docs_for_ba(self, pk):
        try:
            docs = ProjectDocument.objects.filter(
                project__business_area=pk, project_lead_approval_granted=False
            ).distinct()  # Ensure unique documents
        except ProjectDocument.DoesNotExist:
            raise NotFound
        except Exception as e:
            settings.LOGGER.error(f"Error: {e}")
            docs = (
                ProjectDocument.objects.none()
            )  # Return an empty QuerySet on exception
        return docs

    def post(self, req):
        try:
            pksArray = req.data.get("baArray")
            settings.LOGGER.info(
                msg=f"{req.user} is Getting My BA Unapproved Docs: {pksArray}"
            )
            data = {}
            for baPk in pksArray:
                unapproved = self.get_unapproved_docs_for_ba(baPk)
                processed_unapproved = []
                seen_pks = set()
                unlinked_docs = []
                for item in unapproved:
                    if item.pk not in seen_pks:
                        if item.has_project_document_data() == False:
                            unlinked_docs.append(item)
                        else:
                            processed_unapproved.append(item)
                            seen_pks.add(item.pk)
                ser = ProjectDocumentSerializer(processed_unapproved, many=True)
                ser2 = ProjectDocumentSerializer(unlinked_docs, many=True)
                data[baPk] = {
                    "linked": ser.data,
                    "unlinked": ser2.data,
                }
                # ba_name = unapproved[0].business_area
                settings.LOGGER.warning(
                    f"Unapproved Doc Count for BA '{data[baPk]["linked"][0]['project']['business_area']['name']}' ({baPk}): {len(processed_unapproved)}\nUnlinked Doc Count for BA {(len(unlinked_docs))}"
                    if data[baPk]["linked"]
                    else f"Unapproved Doc Count for BA {baPk}: {len(processed_unapproved)}\nUnlinked Doc Count for BA: {(len(unlinked_docs))}"
                )
            return Response(
                data=data,
                status=HTTP_200_OK,
            )
        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"msg": e}, HTTP_400_BAD_REQUEST)


class BusinessAreasProblematicProjects(APIView):
    def get_projects_in_ba_array(self, ba_array):
        try:
            projects = (
                Project.objects.filter(business_area__in=ba_array)
                .select_related("business_area", "image")
                .prefetch_related(
                    "members",  # Prefetch project members
                    "members__user",  # Prefetch the user for each member
                )
            )
        except Project.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            return Project.objects.none()
        return projects

    def get(self, req):
        try:
            # Get business area ID from query parameters (for single BA requests)
            business_area_id = req.query_params.get("business_area_id")
            if not business_area_id:
                return Response(
                    {"error": "business_area_id parameter is required"},
                    status=HTTP_400_BAD_REQUEST,
                )

            settings.LOGGER.info(
                msg=f"{req.user} is Getting Problematic Projects for Business Area {business_area_id}"
            )

            all_projects = self.get_projects_in_ba_array([business_area_id])
            memberless_projects = []
            no_leader_tag_projects = []
            multiple_leader_tag_projects = []
            externally_led_projects = []

            for p in all_projects:
                members = p.members.all()  # No DB hit thanks to prefetch_related
                leader_tag_count = 0
                external_leader = False

                for mem in members:
                    if mem.role == ProjectMember.RoleChoices.SUPERVISING:
                        leader_tag_count += 1
                    if mem.is_leader == True and mem.user.is_staff == False:
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
            settings.LOGGER.error(msg=f"{e}")
            return Response({"msg": str(e)}, status=HTTP_400_BAD_REQUEST)

    def post(self, req):
        try:
            pksArray = req.data.get("baArray")
            settings.LOGGER.info(
                msg=f"{req.user} is Getting My BA Problem Projects: {pksArray}"
            )
            data = {}

            for baPk in pksArray:
                # Optimized query with prefetch
                projects_in_ba = Project.objects.filter(
                    business_area=baPk
                ).prefetch_related(
                    "members",
                    "members__user",
                )

                memberless_projects = []
                no_leader_tag_projects = []
                multiple_leader_tag_projects = []
                externally_led_projects = []

                for p in projects_in_ba:
                    members = p.members.all()  # Now uses prefetched data
                    leader_tag_count = 0
                    external_leader = False

                    for mem in members:
                        if mem.role == ProjectMember.RoleChoices.SUPERVISING:
                            leader_tag_count += 1
                        if mem.is_leader == True:
                            if (
                                mem.user.is_staff == False
                            ):  # No additional query for user
                                external_leader = True

                    # Handle Memberless
                    if len(members) < 1:
                        memberless_projects.append(p)
                    else:
                        # Handle external Leader tag
                        if external_leader:
                            externally_led_projects.append(p)
                        # Handle No Leader Tags
                        if leader_tag_count == 0:
                            no_leader_tag_projects.append(p)
                        elif leader_tag_count > 1:
                            multiple_leader_tag_projects.append(p)

                data[baPk] = {}
                data[baPk]["no_members"] = ProblematicProjectSerializer(
                    memberless_projects, many=True
                ).data
                data[baPk]["no_leader"] = ProblematicProjectSerializer(
                    no_leader_tag_projects, many=True
                ).data
                data[baPk]["external_leader"] = ProblematicProjectSerializer(
                    externally_led_projects, many=True
                ).data
                data[baPk]["multiple_leads"] = ProblematicProjectSerializer(
                    multiple_leader_tag_projects, many=True
                ).data

            return Response(data=data, status=HTTP_200_OK)

        except Exception as e:
            settings.LOGGER.error(msg=f"{e}")
            return Response({"msg": e}, HTTP_400_BAD_REQUEST)


class SetBusinessAreaActive(APIView):
    def go(self, pk):
        try:
            business_area = BusinessArea.objects.get(pk=pk)
        except BusinessArea.DoesNotExist:
            raise NotFound
        return business_area

    def post(self, req, pk):
        ba = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is changing active status of {ba}")
        try:
            ba.is_active = not ba.is_active
            new = ba.save()
            ser = BusinessAreaSerializer(new)
            return Response(
                ser.data,
                HTTP_202_ACCEPTED,
            )
        except Exception as e:
            settings.LOGGER.error(
                msg=f"Error setting active status of Business Area: {ser.errors}"
            )
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================


# region Division Views ====================================================================================================


class Divisions(APIView):
    def get(self, req):
        all = Division.objects.all()
        ser = TinyDivisionSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a division")
        ser = DivisionSerializer(
            data=req.data,
        )
        if ser.is_valid():
            div = ser.save()
            return Response(
                TinyDivisionSerializer(div).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DivisionDetail(APIView):
    def go(self, pk):
        try:
            obj = Division.objects.get(pk=pk)
        except Division.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        div = self.go(pk)
        ser = DivisionSerializer(div)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        div = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting division {div}")
        div.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        div = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating division {div}")
        ser = DivisionSerializer(
            div,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            udiv = ser.save()
            return Response(
                TinyDivisionSerializer(udiv).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DivisionEmailList(APIView):
    def go(self, pk):
        try:
            obj = Division.objects.get(pk=pk)
        except Division.DoesNotExist:
            print("Could not find division", pk)
            raise NotFound
        return obj

    def get_user(self, pk):
        try:
            u = User.objects.get(pk=pk)
        except User.DoesNotExist:
            print("Could not find user", pk)
            raise NotFound
        return u

    def get(self, request, pk):
        division = self.go(pk)
        serializer = TinyDivisionSerializer(division)
        return Response(serializer.data)

    def post(self, request, pk):

        # Get the division
        division = self.go(pk)
        usersArray = request.data.get("usersList", [])

        print(request.data)
        # if not usersArray:
        #     return Response({"error": "No users provided"}, status=HTTP_400_BAD_REQUEST)

        # print("here")
        newUserArray = []
        for u in usersArray:
            try:
                user = self.get_user(u)
                newUserArray.append(user)
            except NotFound:
                return Response(
                    {"error": f"User with pk {u} not found"},
                    status=HTTP_400_BAD_REQUEST,
                )

        try:

            division.directorate_email_list.set(newUserArray)

            # Force a refresh by getting the division again
            division = Division.objects.get(pk=pk)
            serializer = TinyDivisionSerializer(division)

            return Response(serializer.data, status=HTTP_202_ACCEPTED)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


# endregion  =================================================================================================


# region Departmental Service Views ====================================================================================================


class DepartmentalServices(APIView):
    def get(self, req):
        all = DepartmentalService.objects.all()
        ser = TinyDepartmentalServiceSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a departmental service")
        ser = DepartmentalServiceSerializer(
            data=req.data,
        )
        if ser.is_valid():
            service = ser.save()
            return Response(
                TinyDepartmentalServiceSerializer(service).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DepartmentalServiceDetail(APIView):
    def go(self, pk):
        try:
            obj = DepartmentalService.objects.get(pk=pk)
        except DepartmentalService.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        service = self.go(pk)
        ser = DepartmentalServiceSerializer(service)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        service = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting departmental service detail {service}"
        )
        service.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        service = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating departmental service detail {service}"
        )
        ser = DepartmentalServiceSerializer(
            service,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uservice = ser.save()
            return Response(
                TinyDepartmentalServiceSerializer(uservice).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================
