import ast
import json
import os
import uuid
import requests
from rest_framework.views import APIView
from math import ceil

import urllib3
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


from contacts.models import UserContact
from medias.models import UserAvatar
from medias.serializers import TinyUserAvatarSerializer
from medias.views import UserAvatarDetail, UserAvatars
from projects.models import Project, ProjectMember
from .models import User, UserProfile, UserWork
from rest_framework.exceptions import NotFound
from .serializers import (
    PrivateTinyUserSerializer,
    ProfilePageSerializer,
    TinyUserProfileSerializer,
    TinyUserSerializer,
    TinyUserWorkSerializer,
    UpdateMembershipSerializer,
    UpdatePISerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserWorkSerializer,
    # TinyUserProfileSerializer,
    # TinyUserWorkSerializer,
    # UserProfileSerializer,
    # UserSerializer,
    # UserWorkSerializer,
)
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from rest_framework.exceptions import ParseError
from django.contrib.auth import authenticate, login, logout

# import jwt
from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.utils.text import capfirst


class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, req):
        username = req.data.get("username")
        password = req.data.get("password")
        if not username or not password:
            raise ParseError("Username and Password must both be provided!")
        user = authenticate(username=username, password=password)
        if user:
            login(req, user)
            return Response({"ok": "Welcome"})
        else:
            # print("Password Error: no user")
            return Response({"error": "Incorrect Password"})


class Logout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        if settings.DEBUG:
            logout(req)
            return Response({"ok": "True"})
        else:
            if (
                (
                    req.path.startswith("/logout")
                    or req.path.startswith("/api/v1/users/log-out")
                    or req.path.startswith("/api/v1/users/logout")
                )
                and "HTTP_X_LOGOUT_URL" in req.META
                and req.META["HTTP_X_LOGOUT_URL"]
            ):
                print(f"{req.user} is logging out from views")
                data = {"ok": "True", "logoutUrl": req.META["HTTP_X_LOGOUT_URL"]}
                # self.save_request_meta_to_file(request.META)
                logout(req)
                return Response(data, HTTP_200_OK)


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, req):
        user = req.user
        old_password = req.data.get("old_password")
        new_password = req.data.get("new_password")
        if not old_password or not new_password:
            raise ParseError("Passwords not provieded")
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response(status=HTTP_200_OK)
        else:
            raise ParseError("Passwords not provieded")


class CheckEmailExists(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            raise ParseError("Email not provided")

        user_exists = User.objects.filter(email=email).exists()
        return Response(
            {"exists": user_exists},
            status=HTTP_200_OK,
        )


class CheckNameExists(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        if not first_name or not last_name:
            raise ParseError("First name or last name not provided")

        # Capitalize the first letter of first_name and last_name
        capitalized_first_name = capfirst(first_name)
        capitalized_last_name = capfirst(last_name)

        user_exists = User.objects.filter(
            first_name__iexact=capitalized_first_name,
            last_name__iexact=capitalized_last_name,
        ).exists()
        return Response(
            {"exists": user_exists},
            status=HTTP_200_OK,
        )


class Me(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        user = req.user
        ser = ProfilePageSerializer(user)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req):
        user = req.user
        settings.LOGGER.info(msg=f"{req.user} is updating their details")
        ser = TinyUserSerializer(
            user,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            return Response(
                TinyUserSerializer(updated).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class SmallInternalUserSearch(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        page = 1
        page_size = 5
        start = (page - 1) * page_size
        end = start + page_size

        search_term = request.GET.get("searchTerm")
        only_internal = request.GET.get("onlyInternal")
        project_pk = request.GET.get("fromProject")

        try:
            only_internal = ast.literal_eval(only_internal)
        except (ValueError, SyntaxError):
            only_internal = False

        if only_internal == True:
            if project_pk:
                project = Project.objects.get(pk=project_pk)
                users = User.objects.filter(member_of__project=project, is_staff=True)

            else:
                users = User.objects.filter(is_staff=True)

        else:
            users = User.objects.all()

        if search_term:
            # Apply filtering based on the search term
            q_filter = (
                Q(first_name__icontains=search_term)
                | Q(last_name__icontains=search_term)
                | Q(email__icontains=search_term)
                | Q(username__icontains=search_term)
            )

            # Check if the search term has a space
            if " " in search_term:
                first_name, last_name = search_term.split(" ")
                q_filter |= Q(first_name__icontains=first_name) & Q(
                    last_name__icontains=last_name
                )

            users = users.filter(q_filter)

        # Sort users alphabetically based on email
        users = users.order_by("first_name")

        serialized_users = TinyUserSerializer(
            users[start:end], many=True, context={"request": request}
        ).data

        response_data = {"users": serialized_users}

        return Response(response_data, status=HTTP_200_OK)


class Users(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        settings.LOGGER.info(msg=f"{request.user} is viewing/filtering users")
        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = settings.PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size

        search_term = request.GET.get("searchTerm")
        business_area = request.GET.get("businessArea")

        # Get the values of the checkboxes
        only_superuser = bool(request.GET.get("only_superuser", False))
        only_staff = bool(request.GET.get("only_staff", False))
        only_external = bool(request.GET.get("only_external", False))

        # Interaction logic between checkboxes
        if only_external:
            only_staff = False
            only_superuser = False
        elif only_staff or only_superuser:
            only_external = False

        if search_term:
            # Check if there is a space in the search term (fn + ln)
            search_parts = search_term.split(" ", 1)
            # Apply filtering based on the search term
            if len(search_parts) == 2:
                first_name, last_name = search_parts
                users = User.objects.filter(
                    Q(first_name__icontains=first_name)
                    & Q(last_name__icontains=last_name)
                    | Q(email__icontains=search_term)
                    | Q(username__icontains=search_term)
                )

            else:
                # If the search term cannot be split, continue with the existing logic
                users = User.objects.filter(
                    Q(first_name__icontains=search_term)
                    | Q(last_name__icontains=search_term)
                    | Q(email__icontains=search_term)
                    | Q(username__icontains=search_term)
                )

        else:
            users = User.objects.all()

        # Filter users based on checkbox values
        if only_external:
            users = users.filter(is_staff=False)
        elif only_staff:
            users = users.filter(is_staff=True)
        elif only_superuser:
            users = users.filter(is_superuser=True)

        if business_area != "All":
            users = users.filter(work__business_area__pk=business_area).all()

        # Sort users alphabetically based on email
        users = users.order_by("email")

        total_users = users.count()
        total_pages = ceil(total_users / page_size)

        serialized_users = TinyUserSerializer(
            users[start:end], many=True, context={"request": request}
        ).data

        response_data = {
            "users": serialized_users,
            "total_results": total_users,
            "total_pages": total_pages,
        }

        return Response(response_data, status=HTTP_200_OK)

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating user")
        ser = PrivateTinyUserSerializer(
            data=req.data,
        )
        if ser.is_valid():
            try:
                # Ensures everything is rolled back if there is an error.
                with transaction.atomic():
                    new_user = ser.save(
                        first_name=req.data.get("firstName"),
                        last_name=req.data.get("lastName"),
                    )

                    # Creates UserWork entry
                    UserWork.objects.create(user=new_user)
                    # Creates UserProfile entry
                    UserProfile.objects.create(user=new_user)
                    # Creates UserContact entry
                    UserContact.objects.create(user=new_user)

                    new_user.set_password(settings.EXTERNAL_PASS)
                    new_user.save()
                    ser = TinyUserSerializer(new_user)
                    return Response(
                        ser.data,
                        status=HTTP_201_CREATED,
                    )
            except Exception as e:
                settings.LOGGER.error(msg=f"{e}")
                raise ParseError(e)
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class ToggleUserActive(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound
        return obj

    def post(self, req, pk):
        user = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is setting user's active state: {user}")
        user.is_active = not user.is_active
        updated = user.save()

        ser = UserSerializer(updated).data
        return Response(
            ser,
            HTTP_202_ACCEPTED,
        )


class UserDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        user = self.go(pk)
        ser = ProfilePageSerializer(
            user,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        user = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting user: {user}")
        user.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        user = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating user: {user}")
        ser = UserSerializer(
            user,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_user = ser.save()
            return Response(
                TinyUserSerializer(u_user).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class UserProfileDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = UserProfile.objects.get(pk=pk)
        except UserProfile.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        profile = self.go(pk)
        ser = UserProfileSerializer(
            profile,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        profile = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting profile {profile}")
        profile.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        profile = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating userprofile {profile}")
        ser = UserProfileSerializer(
            profile,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uprofile = ser.save()
            return Response(
                TinyUserProfileSerializer(uprofile).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class UserProfiles(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = UserProfile.objects.all()
        ser = TinyUserProfileSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting user profile")
        ser = UserProfileSerializer(
            data=req.data,
        )
        if ser.is_valid():
            profile = ser.save()
            return Response(
                TinyUserProfileSerializer(profile).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.errors(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class UserWorkDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = UserWork.objects.get(pk=pk)
        except UserWork.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        work = self.go(pk)
        ser = UserWorkSerializer(
            work,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        work = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting work {work}")
        work.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        work = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating work of {work}")
        ser = UserWorkSerializer(
            work,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uwork = ser.save()
            return Response(
                TinyUserWorkSerializer(uwork).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.errors(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class UserWorks(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        all = UserWork.objects.all()
        ser = TinyUserWorkSerializer(
            all,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating user work")
        ser = UserWorkSerializer(
            data=req.data,
        )
        if ser.is_valid():
            work = ser.save()
            return Response(
                TinyUserWorkSerializer(work).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class DirectorateUsers(ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = TinyUserSerializer

    def get_queryset(self):
        user_works = UserWork.objects.filter(business_area__name="Directorate")
        user_ids = user_works.values_list("user", flat=True)
        return User.objects.filter(id__in=user_ids)


class UpdatePersonalInformation(APIView):
    def go(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def get(self, req, pk):
        user = self.go(pk)
        ser = UpdatePISerializer(user)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req, pk):
        user = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating personal information of {user}"
        )
        title = req.data.get("title")
        phone = req.data.get("phone")
        fax = req.data.get("fax")
        updated_data = {}

        if title is not None and title != "":
            updated_data["title"] = title

        if phone is not None and phone != "":
            updated_data["phone"] = phone

        if fax is not None and fax != "":
            updated_data["fax"] = fax

        ser = UpdatePISerializer(
            user,
            data=updated_data,
            partial=True,
        )

        if ser.is_valid():
            updated_user = ser.save()
            u_ser = UpdatePISerializer(updated_user).data
            return Response(
                u_ser,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.info(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class SwitchAdmin(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def post(self, req, pk):
        user = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is changing user's admin status {user}")

        # Toggle the is_admin attribute
        user.is_superuser = not user.is_superuser
        user.save()

        return Response(
            {"is_admin": user.is_superuser},
            status=HTTP_200_OK,
        )


class UpdateProfile(APIView):
    def go(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def is_valid_image_extension(self, filename):
        valid_extensions = (".jpg", ".jpeg", ".png")
        return filename.lower().endswith(valid_extensions)

    def get(self, req, pk):
        user = self.go(pk)
        ser = ProfilePageSerializer(user)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def handle_image(self, image):
        if isinstance(image, str):
            return image
        elif image is not None:
            # Get the original file name with extension
            original_filename = image.name

            # Specify the subfolder within your media directory
            subfolder = "user_avatars"

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

    def put(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is updating their profile")
        image = req.data.get("image")
        if image:
            if isinstance(image, str) and (
                image.startswith("http://") or image.startswith("https://")
            ):
                # URL provided, validate the URL
                if not image.lower().endswith((".jpg", ".jpeg", ".png")):
                    error_message = "The URL is not a valid photo file"
                    return Response(error_message, status=HTTP_400_BAD_REQUEST)

        about = req.data.get("about")
        expertise = req.data.get("expertise")
        user = self.go(pk)
        user_avatar_post_view = UserAvatars()
        user_avatar_put_view = UserAvatarDetail()
        avatar_exists = UserAvatar.objects.filter(user=user).first()

        # If user didn't update the image
        if image is None:
            updated_data = {}
            if about:
                updated_data["about"] = about
            if expertise:
                updated_data["expertise"] = expertise

            ser = UpdateProfileSerializer(
                user,
                data=updated_data,
                partial=True,
            )
            if ser.is_valid():
                updated_user = ser.save()
                u_ser = UpdateProfileSerializer(updated_user).data
                return Response(
                    u_ser,
                    status=HTTP_202_ACCEPTED,
                )
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )

        # If user updated the image
        else:
            if avatar_exists:
                # Prep the data for if an avatar exists already (put)

                try:
                    avatar_data = {
                        "file": self.handle_image(image),
                    }
                except ValueError as e:
                    error_message = str(e)
                    response_data = {"error": error_message}
                    return Response(response_data, status=HTTP_400_BAD_REQUEST)

                # Create the image with prepped data
                try:
                    for key, value in avatar_data.items():
                        setattr(avatar_exists, key, value)
                    avatar_exists.save()
                    avatar_response = TinyUserAvatarSerializer(avatar_exists).data
                except Exception as e:
                    settings.LOGGER.error(msg=f"{ser.errors}")
                    response_data = {
                        "error": str(e)
                    }  # Create a response data dictionary
                    return Response(
                        response_data, status=HTTP_500_INTERNAL_SERVER_ERROR
                    )

            else:
                try:
                    # Prep the data for if an avatar doesnt exist (post)
                    avatar_data = {
                        # "old_file": None,
                        "file": self.handle_image(image),
                        "user": user,
                    }
                except ValueError as e:
                    error_message = str(e)
                    response_data = {"error": error_message}
                    return Response(response_data, status=HTTP_400_BAD_REQUEST)

                # Create the image with prepped data
                try:
                    new_avatar_instance = UserAvatar.objects.create(**avatar_data)
                    avatar_response = TinyUserAvatarSerializer(new_avatar_instance).data

                except Exception as e:
                    settings.LOGGER.error(msg=f"{e}")
                    response_data = {
                        "error": str(e)
                    }  # Create a response data dictionary
                    return Response(
                        response_data, status=HTTP_500_INTERNAL_SERVER_ERROR
                    )

            updated_data = {}

            if avatar_response["pk"] is not None and avatar_response["pk"] != "":
                updated_data["image"] = avatar_response["pk"]
            elif image is not None and image != "":
                updated_data["image"] = image

            if about:
                updated_data["about"] = about
            if expertise:
                updated_data["expertise"] = expertise

            ser = UpdateProfileSerializer(
                user,
                data=updated_data,
                partial=True,
            )
            if ser.is_valid():
                updated_user = ser.save()
                u_ser = UpdateProfileSerializer(updated_user).data
                return Response(
                    u_ser,
                    status=HTTP_202_ACCEPTED,
                )
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )


class UpdateMembership(APIView):
    def go(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFound

    def get(self, req, pk):
        user = self.go(pk)
        ser = UpdateMembershipSerializer(user)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def put(self, req, pk):
        user = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating user membership {user}")
        user_work = user.work

        # Convert primary key values to integers

        if user.is_staff:
            user_pk = int(req.data.get("user_pk")) if req.data.get("user_pk") else 0
            branch_pk = (
                int(req.data.get("branch_pk")) if req.data.get("branch_pk") else 0
            )
            business_area_pk = (
                int(req.data.get("business_area"))
                if req.data.get("business_area")
                else 0
            )
            affiliation_pk = (
                int(req.data.get("affiliation")) if req.data.get("affiliation") else 0
            )

            data_obj = {}
            data_obj["user_pk"] = user_pk
            if branch_pk != 0:
                data_obj["branch"] = branch_pk
            if business_area_pk != 0:
                data_obj["business_area"] = business_area_pk
            if affiliation_pk != 0:
                data_obj["affiliation"] = affiliation_pk
            else:
                data_obj["affiliation"] = None

            ser = UpdateMembershipSerializer(user_work, data=data_obj)
            if ser.is_valid():
                updated = ser.save()
                serialized = UpdateMembershipSerializer(updated).data
                print(serialized)
                return Response(
                    serialized,
                    status=HTTP_202_ACCEPTED,
                )
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )
        else:
            settings.LOGGER.warning(msg=f"This user is not staff")
            return Response(
                "This user is not staff",
                status=HTTP_200_OK,
            )
