import ast
import json
import os
import pprint
import uuid
import requests
from agencies.models import Affiliation, Agency, Branch, BusinessArea
from projects.serializers import (
    MiniUserSerializer,
    ProjectDataTableSerializer,
    ProjectSerializer,
    TinyProjectSerializer,
    UserProfileProjectSerializer,
)
from rest_framework.views import APIView
from math import ceil

import urllib3
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from config.helpers import get_encoded_image
from django.template.loader import render_to_string
from django.core.mail import send_mail, send_mass_mail

from contacts.models import UserContact
from medias.models import UserAvatar
from medias.serializers import TinyUserAvatarSerializer
from medias.views import UserAvatarDetail, UserAvatars
from projects.models import Project, ProjectMember
from .models import (
    EducationEntry,
    EmploymentEntry,
    KeywordTag,
    PublicStaffProfile,
    User,
    UserProfile,
    UserWork,
)
from rest_framework.exceptions import NotFound
from .serializers import (
    EducationEntryCreationSerializer,
    EducationEntrySerializer,
    EmploymentEntryCreationSerializer,
    EmploymentEntrySerializer,
    ITAssetSerializer,
    PrivateTinyUserSerializer,
    ProfilePageSerializer,
    StaffProfileCVSerializer,
    StaffProfileCreationSerializer,
    StaffProfileHeroSerializer,
    StaffProfileOverviewSerializer,
    StaffProfileSerializer,
    TinyStaffProfileSerializer,
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
    HTTP_401_UNAUTHORIZED,
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


# only in dev
class Logout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, req):
        if settings.DEBUG:
            logout(req)
            return Response({"ok": "True"})
        else:
            if "HTTP_X_LOGOUT_URL" in req.META and req.META["HTTP_X_LOGOUT_URL"]:
                settings.LOGGER.info(msg=f"{req.user} is logging out...")
                logout(req)
                data = {"logoutUrl": req.META["HTTP_X_LOGOUT_URL"]}
                return Response(data=data, status=HTTP_200_OK)
            # if (
            #     (
            #         req.path.startswith("/logout")
            #         or req.path.startswith("/api/v1/users/log-out")
            #         or req.path.startswith("/api/v1/users/logout")
            #     )
            #     and "HTTP_X_LOGOUT_URL" in req.META
            #     and req.META["HTTP_X_LOGOUT_URL"]
            # ):
            #     print(f"{req.user} is logging out from views")
            #     data = {"ok": "True", "logoutUrl": req.META["HTTP_X_LOGOUT_URL"]}
            #     # self.save_request_meta_to_file(request.META)
            #     logout(req)
            #     return Response(data, HTTP_200_OK)


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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
                    | Q(display_first_name__icontains=first_name)
                    & Q(display_last_name__icontains=last_name)
                    | Q(email__icontains=search_term)
                    | Q(username__icontains=search_term)
                )

            else:
                # If the search term cannot be split, continue with the existing logic
                users = User.objects.filter(
                    Q(first_name__icontains=search_term)
                    | Q(last_name__icontains=search_term)
                    | Q(display_first_name__icontains=search_term)
                    | Q(display_last_name__icontains=search_term)
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
                    staff = req.data.get("isStaff")

                    first_name = req.data.get("firstName").capitalize()
                    last_name = req.data.get("lastName").capitalize()
                    if staff:
                        new_user = ser.save(
                            first_name=first_name,
                            last_name=last_name,
                            display_first_name=first_name,
                            display_last_name=last_name,
                            is_staff=True,
                        )
                    else:
                        new_user = ser.save(
                            first_name=first_name,
                            last_name=last_name,
                            display_first_name=first_name,
                            display_last_name=last_name,
                        )

                    # Extracting the work details from the request data
                    branch_id = req.data.get("branch")
                    business_area_id = req.data.get("businessArea")
                    affiliation_id = req.data.get("affiliation")
                    role = req.data.get(
                        "role", ""
                    )  # Default to empty string if role is not provided

                    # Initialize variables for related objects
                    branch = None
                    business_area = None
                    affiliation = None

                    # Retrieve related objects if IDs are provided
                    if branch_id:
                        branch = Branch.objects.get(pk=branch_id)
                    if business_area_id:
                        business_area = BusinessArea.objects.get(pk=business_area_id)
                    if affiliation_id:
                        affiliation = Affiliation.objects.get(pk=affiliation_id)

                    # Creates UserWork entry
                    if staff:
                        agency = Agency.objects.get(pk=1)
                        if branch and business_area:
                            print(branch, business_area)
                            UserWork.objects.create(
                                user=new_user,
                                agency=agency,
                                branch=branch,
                                business_area=business_area,
                                affiliation=affiliation,
                                role="",
                            )
                        else:
                            UserWork.objects.create(user=new_user)
                    else:
                        if affiliation:
                            affiliation = Affiliation.objects.get(pk=affiliation_id)
                            UserWork.objects.create(
                                user=new_user,
                                branch=None,
                                business_area=None,
                                affiliation=affiliation,
                                role=None,
                            )
                        else:
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
    permission_classes = [IsAuthenticated]

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


class UsersProjects(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            data = ProjectMember.objects.filter(user=pk)
        except ProjectMember.DoesNotExist:
            raise NotFound
        return data

    def get(self, req, pk):
        users_memberships = self.go(pk=pk)
        if len(users_memberships) > 0:
            user_obj = users_memberships[0].user
            settings.LOGGER.info(
                msg=f"{req.user} is viewing {user_obj} and their projects"
            )
        else:
            settings.LOGGER.info(
                msg=f"{req.user} is viewing user with pk {pk} and their projects (none)"
            )
        projects_with_roles = [
            (membership.project, membership.role) for membership in users_memberships
        ]

        serialized_projects = ProjectDataTableSerializer(
            [proj for proj, _ in projects_with_roles],
            many=True,
            context={"projects_with_roles": projects_with_roles},
        )

        # print(serialized_projects)
        return Response(serialized_projects.data, HTTP_200_OK)

        # interface ITinyProjectData {
        # pk?: number | undefined;
        # id?: number | undefined;
        # title: string;
        # }


# =================================================
class MyStaffProfile(APIView):
    permission_classes = [AllowAny]

    def go(self, pk):
        try:
            obj = PublicStaffProfile.objects.get(user=pk)
        except PublicStaffProfile.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        staff_profile = self.go(pk)
        settings.LOGGER.info(msg=f"(PUBLIC) {req.user} is viewing their staff profile")
        ser = StaffProfileSerializer(
            staff_profile,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )


class StaffProfiles(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(
            msg=f"(Public) {req.user} is viewing/filtering STAFF PROFILES"
        )
        try:
            page = int(req.query_params.get("page", 1))
        except ValueError:
            # If the user sends a non-integer value as the page parameter
            page = 1

        page_size = 16
        start = (page - 1) * page_size
        end = start + page_size

        search_term = req.GET.get("searchTerm")

        if search_term:
            # Check if there is a space in the search term (fn + ln)
            search_parts = search_term.split(" ", 1)
            # Apply filtering based on the search term
            if len(search_parts) == 2:
                first_name, last_name = search_parts
                users = User.objects.filter(is_staff=True).filter(
                    Q(first_name__icontains=first_name)
                    & Q(last_name__icontains=last_name)
                )

            else:
                # If the search term cannot be split, continue with the existing logic
                users = User.objects.filter(is_staff=True).filter(
                    Q(first_name__icontains=search_term)
                    | Q(last_name__icontains=search_term)
                )

        else:
            users = User.objects.filter(is_staff=True).all()

        # Sort users alphabetically based on email
        users = users.order_by("first_name")

        total_users = users.count()
        total_pages = ceil(total_users / page_size)

        serialized_users = TinyStaffProfileSerializer(
            users[start:end], many=True, context={"request": req}
        ).data

        response_data = {
            "users": serialized_users,
            "total_results": total_users,
            "page": page,
            "total_pages": total_pages,
        }

        return Response(response_data, status=HTTP_200_OK)

    def post(self, req, post):
        settings.LOGGER.info(msg=f"{req.user} is creating staff profile")
        keyword_tags_data = req.data.get("keyword_tags", [])

        processed_tags = []
        for tag_data in keyword_tags_data:
            if isinstance(tag_data, dict):  # Ensure we're handling a dictionary
                tag_name = tag_data.get("name")
                # tag_pk = tag_data.get("pk")

                # if tag_pk:
                #     processed_tags.append({"pk": tag_pk, "name": tag_name})
                if tag_name:  # Create or get the tag by name if pk is not provided
                    tag, created = KeywordTag.objects.get_or_create(name=tag_name)
                    processed_tags.append({"pk": tag.pk, "name": tag.name})

        req.data["keyword_tags"] = processed_tags

        ser = StaffProfileCreationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            try:
                # Ensures everything is rolled back if there is an error.
                with transaction.atomic():
                    # Save the new staff profile instance
                    staff_profile = ser.save()

                    # Return the newly created staff profile data
                    return Response(
                        StaffProfileCreationSerializer(staff_profile).data,
                        status=HTTP_201_CREATED,
                    )

            except Exception as e:
                # If there is any exception, log it and return an error response
                settings.LOGGER.error(msg=f"Error creating staff profile: {str(e)}")
                return Response(
                    {"detail": "An error occurred while creating the staff profile."},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # If the serializer is not valid, return the errors
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class StaffProfileDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = PublicStaffProfile.objects.get(pk=pk)
        except PublicStaffProfile.DoesNotExist:
            raise NotFound
        return obj

    def check_tag_usage(self, tag_name):
        try:
            tag = KeywordTag.objects.get(name=tag_name)
        except KeywordTag.DoesNotExist:
            return False  # Tag doesn't exist, so it isn't in use

        return (
            tag.staff_profiles.exists()
        )  # Returns True if the tag is used in any profile

    def get(self, req, pk):
        staff_profile = self.go(pk)
        settings.LOGGER.info(
            msg=f"(PUBLIC) {req.user} is viewing Staff profile of: {staff_profile.user.first_name} {user.last_name}"
        )
        ser = StaffProfileSerializer(
            staff_profile,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        staff_profile = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting staff profile: {staff_profile}"
        )
        staff_profile.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        staff_profile = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating staff profile: {staff_profile}"
        )

        keyword_tags_data = req.data.get("keyword_tags")

        if keyword_tags_data:
            processed_tags = []
            for tag_data in keyword_tags_data:
                if isinstance(tag_data, dict):  # Ensure we're handling a dictionary
                    tag_name = tag_data.get("name")
                    # tag_pk = tag_data.get("pk")

                    # if tag_pk:
                    #     processed_tags.append({"pk": tag_pk, "name": tag_name})
                    if tag_name:  # Create or get the tag by name if pk is not provided
                        tag, created = KeywordTag.objects.get_or_create(name=tag_name)
                        processed_tags.append({"pk": tag.pk, "name": tag.name})

            req.data["keyword_tags"] = processed_tags

        ser = StaffProfileSerializer(
            staff_profile,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            u_staff_profile = ser.save()
            # After saving, check if any old tags are no longer in use and delete them
            all_tags = KeywordTag.objects.all()
            for tag in all_tags:
                if not self.check_tag_usage(tag.name):
                    tag.delete()

            return Response(
                StaffProfileSerializer(u_staff_profile).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class StaffProfileHeroDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            profile = PublicStaffProfile.objects.get(user=pk)
        except PublicStaffProfile.DoesNotExist:
            raise NotFound
        return profile

    def get(self, req, pk):
        settings.LOGGER.info(
            msg=f"(PUBLIC) {req.user} is getting Hero Data for a user with id {pk}"
        )
        profile = self.go(pk)
        ser = StaffProfileHeroSerializer(profile)
        return Response(ser.data, status=HTTP_200_OK)


class StaffProfileOverviewDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            profile = PublicStaffProfile.objects.get(user=pk)
        except PublicStaffProfile.DoesNotExist:
            raise NotFound
        return profile

    def get(self, req, pk):
        settings.LOGGER.info(
            msg=f"(PUBLIC) {req.user} is getting Overview Data for a user with id {pk}"
        )
        profile = self.go(pk)
        ser = StaffProfileOverviewSerializer(profile)
        return Response(ser.data, status=HTTP_200_OK)


class StaffProfileCVDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            profile = PublicStaffProfile.objects.get(user=pk)
        except PublicStaffProfile.DoesNotExist:
            raise NotFound
        return profile

    def get(self, req, pk):
        settings.LOGGER.info(
            msg=f"(PUBLIC) {req.user} is getting CV Data for a user with id {pk}"
        )
        profile = self.go(pk)
        ser = StaffProfileCVSerializer(profile)
        return Response(ser.data, status=HTTP_200_OK)


class PublicEmailStaffMember(APIView):
    permission_classes = [AllowAny]

    def go(self, pk):
        try:
            user = User.objects.filter(pk=pk).first()
        except User.DoesNotExist:
            raise NotFound
        return user

    def post(self, req, pk):
        settings.LOGGER.info(
            msg=f"(PUBLIC) {req.user} is attempting to use '{req.data['senderEmail']}' to send an email to a staff member"
        )

        try:
            # Fetch the staff member
            staff_member = User.objects.get(pk=pk)
            ser = MiniUserSerializer(staff_member)
            recipient_name = (
                f"{staff_member.display_first_name} {staff_member.display_last_name}"
            )
            recipient_email = staff_member.email

            # Log email sending attempt
            settings.LOGGER.warning(
                msg=f"(PUBLIC) {req.data['senderEmail']} sent a public email to {recipient_email}"
            )

            # Email details
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [recipient_email]
            templ = "./email_templates/staff_profile_email.html"

            # Template context
            template_props = {
                "recipient_name": recipient_name,
                "staff_message": req.data.get("message"),
                "public_users_listed_email": req.data.get("senderEmail"),
                "dbca_image_path": get_encoded_image(),
            }

            # Render the email template
            template_content = render_to_string(templ, template_props)

            if settings.DEBUG == False:
                if settings.ON_TEST_NETWORK != True:
                    print(f"PRODUCTION: Sending email to {recipient_name}")
                    try:
                        send_mail(
                            "Staff Profile Message",
                            template_content,  # plain text version
                            from_email,
                            to_email,
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
                else:
                    print(f"LIVE TEST: Sending email to {recipient_name}")
                    try:
                        send_mail(
                            "Staff Profile Message",
                            template_content,  # plain text version
                            from_email,
                            ["jarid.prince@dbca.wa.gov.au"],
                            fail_silently=False,  # Set this to False to see errors
                            html_message=template_content,
                        )
                    except Exception as e:
                        settings.LOGGER.error(
                            msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters (the device you are running this from isn't on OIM's network).\nThis will work in production."
                        )
                        return Response(
                            {"error": str(e)},
                            status=HTTP_400_BAD_REQUEST,
                        )
            else:  # Test environment
                # Simulate sending the email
                print("THIS IS A SIMULATION")
                print(f"DEV: Sending email to {recipient_name}")
                print(
                    {
                        "to_email": to_email,
                        "recipient_name": recipient_name,
                        "public_users_listed_email": req.data.get("senderEmail"),
                    }
                )

            return Response(
                "Email Sent!",
                status=HTTP_202_ACCEPTED,
            )

        except User.DoesNotExist:
            settings.LOGGER.error(f"(PUBLIC) Staff member with pk {pk} not found.")
            return Response(
                {"error": "Staff member not found"},
                status=HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            settings.LOGGER.error(
                msg=f"(PUBLIC) an error occurred sending a public email:\n{e}"
            )
            return Response(
                {"error": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )


# =================================================


class StaffProfileEmploymentEntries(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(msg=f"(Public) {req.user} is viewing employment entries")
        entries = EmploymentEntry.objects.all()
        serialized_entries = EmploymentEntrySerializer(
            entries, many=True, context={"request": req}
        ).data

        return Response(serialized_entries, status=HTTP_200_OK)

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating employment entry")
        ser = EmploymentEntryCreationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            try:
                # Ensures everything is rolled back if there is an error.
                with transaction.atomic():
                    # Save the new staff profile instance
                    employment_entry = ser.save()

                    # Return the newly created staff profile data
                    return Response(ser.data, status=HTTP_201_CREATED)

            except Exception as e:
                # If there is any exception, log it and return an error response
                settings.LOGGER.error(msg=f"Error creating employment entry: {str(e)}")
                return Response(
                    {
                        "detail": "An error occurred while creating the employment entry."
                    },
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # If the serializer is not valid, return the errors
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class StaffProfileEducationEntries(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        settings.LOGGER.info(msg=f"(Public) {req.user} is viewing education entries")
        entries = EducationEntry.objects.all()
        serialized_entries = EducationEntrySerializer(
            entries, many=True, context={"request": req}
        ).data

        return Response(serialized_entries, status=HTTP_200_OK)

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating education entry")
        # pprint.pprint(req.data)
        ser = EducationEntryCreationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            try:
                # Ensures everything is rolled back if there is an error.
                with transaction.atomic():
                    # Save the new staff profile instance
                    education_entry = ser.save()

                    # Return the newly created staff profile data
                    return Response(ser.data, status=HTTP_201_CREATED)

            except Exception as e:
                # If there is any exception, log it and return an error response
                settings.LOGGER.error(msg=f"Error creating education entry: {str(e)}")
                return Response(
                    {"detail": "An error occurred while creating the education entry."},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # If the serializer is not valid, return the errors
            print(ser.errors)
            return Response(ser.errors, status=HTTP_400_BAD_REQUEST)


class StaffProfileEducationEntryDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = EducationEntry.objects.get(pk=pk)
        except EducationEntry.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        entry = self.go(pk)
        ser = EducationEntrySerializer(
            entry,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        entry = self.go(pk)
        if req.user.is_superuser == False and req.user is not entry.public_profile.user:
            return Response(
                data={"error": True},
                status=HTTP_401_UNAUTHORIZED,
            )
        settings.LOGGER.info(msg=f"{req.user} is deleting education {entry}")
        entry.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        entry = self.go(pk)
        if req.user.is_superuser == False and req.user is not entry.public_profile.user:
            return Response(
                data={"error": True},
                status=HTTP_401_UNAUTHORIZED,
            )
        settings.LOGGER.info(msg=f"{req.user} is updating education {entry}")
        ser = EducationEntrySerializer(
            entry,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uentry = ser.save()
            return Response(
                EducationEntrySerializer(uentry).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class StaffProfileEmploymentEntryDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = EmploymentEntry.objects.get(pk=pk)
        except EmploymentEntry.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        entry = self.go(pk)
        ser = EmploymentEntrySerializer(
            entry,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):

        entry = self.go(pk)
        if req.user.is_superuser == False and req.user is not entry.public_profile.user:
            return Response(
                data={"error": True},
                status=HTTP_401_UNAUTHORIZED,
            )
        settings.LOGGER.info(msg=f"{req.user} is deleting employment {entry}")
        entry.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):

        entry = self.go(pk)
        if req.user.is_superuser == False and req.user is not entry.public_profile.user:
            return Response(
                data={"error": True},
                status=HTTP_401_UNAUTHORIZED,
            )
        settings.LOGGER.info(msg=f"{req.user} is updating employment {entry}")
        ser = EmploymentEntrySerializer(
            entry,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            uentry = ser.save()
            return Response(
                EmploymentEntrySerializer(uentry).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# Getting a user's specific items (view) ===============
class UserStaffEmploymentEntries(APIView):
    def go(self, user_pk):
        try:
            entries = EmploymentEntry.objects.filter(user=user_pk)
        except EmploymentEntry.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            raise Exception(e)
        return entries

    def get(self, req, pk):
        users_employment = self.go(user_pk=pk)
        ser = EmploymentEntrySerializer(users_employment, many=True)
        return Response(ser.data, status=HTTP_200_OK)


class UserStaffEducationEntries(APIView):
    def go(self, user_pk):
        try:
            entries = EducationEntry.objects.filter(user=user_pk)
        except EducationEntry.DoesNotExist:
            raise NotFound
        except Exception as e:
            print(e)
            raise Exception(e)
        return entries

    def get(self, req, pk):
        users_employment = self.go(user_pk=pk)
        ser = EducationEntrySerializer(users_employment, many=True)
        return Response(ser.data, status=HTTP_200_OK)


class ITAssets(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_it_assets(self, pk):
        try:
            email = User.objects.get(pk=pk).email  # Fetch email using primary key
            response = requests.get(
                "https://itassets.dbca.wa.gov.au/api/v3/departmentuser/"
            )
            print(response)
            response.raise_for_status()  # Raise an error for bad HTTP status codes

            data = response.json()  # Assuming the response is in JSON format

            # Filter the data by email
            filtered_data = [item for item in data if item.get("email") == email]

            if not filtered_data:
                raise NotFound(f"No data found for email: {email}")
        except requests.exceptions.HTTPError as http_err:
            # raise Exception(f"HTTP error occurred: {http_err}")
            return Response(
                {"error": f"HTTP error occurred: {http_err}"},
                status=HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # raise Exception(f"An error occurred: {e}")
            return Response(
                {"error": f"An error occurred: {e}"}, status=HTTP_400_BAD_REQUEST
            )

        return filtered_data

    def get(self, request, pk):
        settings.LOGGER.info(
            msg=f"{request.user} is getting IT assets for a user with id {pk}"
        )

        filtered_data = self.get_it_assets(pk)

        # Check if filtered_data is a Response object (which indicates an error)
        if isinstance(filtered_data, Response):
            return filtered_data

        # Serialize the filtered data
        serializer = ITAssetSerializer(filtered_data, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


# ===================================================


class UserDetail(APIView):
    permission_classes = [IsAuthenticated]

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
        print("NEWDATA", req.data)
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]
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
        display_first_name = req.data.get("display_first_name")
        display_last_name = req.data.get("display_last_name")
        print(display_first_name, display_last_name)
        updated_data = {}

        if display_first_name is not None and display_first_name != "":
            updated_data["display_first_name"] = display_first_name
        if display_last_name is not None and display_last_name != "":
            updated_data["display_last_name"] = display_last_name

        if title is not None and title != "":
            updated_data["title"] = title

        if phone is not None and phone != "":
            updated_data["phone"] = phone

        if fax is not None and fax != "":
            updated_data["fax"] = fax

        print(updated_data)

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


class RemoveAvatar(APIView):
    def go(self, pk):
        pass

    def post(self, req, pk):
        settings.LOGGER.info(msg=f"{req.user} is deleting avatar for user with pk {pk}")
        avatar_exists = UserAvatar.objects.filter(user=pk).first()
        if avatar_exists:
            avatar_exists.delete()

        return Response(
            HTTP_204_NO_CONTENT,
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
            data_obj = {}
            affiliation_pk = (
                int(req.data.get("affiliation")) if req.data.get("affiliation") else 0
            )
            if affiliation_pk != 0:
                data_obj["affiliation"] = affiliation_pk

            ser = UpdateMembershipSerializer(
                user_work,
                data=data_obj,
                partial=True,
            )
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

            settings.LOGGER.warning(msg=f"This user is not staff")

            return Response(
                "This user is not staff",
                status=HTTP_200_OK,
            )
