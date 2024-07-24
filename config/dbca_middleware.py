import os
from django import http, VERSION
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.backends import ModelBackend
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import login, logout, get_user_model
from agencies.models import Agency
from contacts.models import UserContact
from django.db import transaction
from rest_framework.exceptions import ParseError
from django.conf import settings

from users.models import UserProfile, UserWork
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
)

User = get_user_model()


# class DBCAMiddleware(MiddlewareMixin):
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def create_user_and_associated_entries(self, request, attributemap):
#         try:
#             with transaction.atomic():
#                 user = User.objects.create_user(
#                     username=attributemap["username"],
#                     first_name=attributemap["first_name"],
#                     last_name=attributemap["last_name"],
#                     email=attributemap["email"],
#                 )
#                 agency_instance = Agency.objects.get(pk=1)
#                 UserWork.objects.create(user=user, agency=agency_instance)
#                 UserProfile.objects.create(user=user)
#                 UserContact.objects.create(user=user)

#                 user.is_staff = True
#                 user.set_password(settings.EXTERNAL_PASS)
#                 user.save()
#                 return user
#         except Exception as e:
#             raise ParseError(str(e))

#     def save_request_meta_to_file(self, meta_data):
#         file_path = os.path.join(settings.BASE_DIR, "requestsMeta.txt")
#         print(f"WRITING UP META TO: {file_path}")
#         mode = "w+"
#         with open(file_path, mode) as file:
#             file.write(str(meta_data) + "\n")

#     def __call__(self, request):
#         if (
#             "HTTP_REMOTE_USER" not in request.META
#             or not request.META["HTTP_REMOTE_USER"]
#         ):
#             return self.get_response(request)

#         # Check to see if user is authenticated
#         user_auth = request.user.is_authenticated
#         # If authenticated, get the user and update the last login
#         if not user_auth:
#             attributemap = {
#                 "username": "HTTP_REMOTE_USER",
#                 "last_name": "HTTP_X_LAST_NAME",
#                 "first_name": "HTTP_X_FIRST_NAME",
#                 "email": "HTTP_X_EMAIL",
#             }

#             for key, value in attributemap.items():
#                 if value in request.META:
#                     attributemap[key] = request.META[value]

#             # If there is an email in the attribute map (registered user), log them in
#             if (
#                 attributemap["email"]
#                 and User.objects.filter(email__iexact=attributemap["email"]).exists()
#             ):
#                 user = User.objects.filter(email__iexact=attributemap["email"])[0]
#                 user.backend = "django.contrib.auth.backends.ModelBackend"
#                 login(request, user)
#             elif (
#                 User.__name__ != "EmailUser"
#                 and User.objects.filter(
#                     username__iexact=attributemap["username"]
#                 ).exists()
#             ):
#                 user = User.objects.filter(username__iexact=attributemap["username"])[0]

#             # If they are not a registered user, create an account
#             else:
#                 user = self.create_user_and_associated_entries(request, attributemap)
#                 user.__dict__.update(attributemap)
#                 # Set is_staff to True
#                 user.is_staff = True
#                 user.save()
#                 user.backend = "django.contrib.auth.backends.ModelBackend"
#                 login(request, user)

#         else:
#             # un = request.META.get("HTTP_REMOTE_USER")
#             # fn = request.META.get("HTTP_X_FIRST_NAME")
#             # ln = request.META.get("HTTP_X_LAST_NAME")
#             em = request.META.get("HTTP_X_EMAIL")

#             # fn and ln and un and
#             if em:
#                 user = User.objects.filter(username=em).first()
#                 if user:
#                     request.user = user
#                     # Logout user if requested url is logout
#                     if (
#                         (
#                             request.path.startswith("/logout")
#                             or request.path.startswith("/api/v1/users/log-out")
#                             or request.path.startswith("/api/v1/users/logout")
#                         )
#                         and "HTTP_X_LOGOUT_URL" in request.META
#                         and request.META["HTTP_X_LOGOUT_URL"]
#                     ):
#                         settings.LOGGER.info(
#                             msg=f"{request.user} is logging out from call"
#                         )
#                         # self.save_request_meta_to_file(request.META)
#                         logout(request)
#                         data = {"logoutUrl": request.META["HTTP_X_LOGOUT_URL"]}
#                         return HttpResponse(data, HTTP_200_OK)

#                     else:
#                         # Otherwise continue with original req
#                         user.save(update_fields=["last_login"])
#                         return self.get_response(request)

#             return self.get_response(request)


class DBCAMiddleware(MiddlewareMixin):
    """Django middleware to process HTTP requests containing headers set by the Auth2
    SSO service, specificially:
    - `HTTP_REMOTE_USER`
    - `HTTP_X_LAST_NAME`
    - `HTTP_X_FIRST_NAME`
    - `HTTP_X_EMAIL`
    The middleware assesses requests containing these headers, and (having deferred user
    authentication to the upstream service), retrieves the local Django User and logs
    the user in automatically.
    If the request path starts with one of the defined logout paths and a `HTTP_X_LOGOUT_URL`
    value is set in the response, log out the user and redirect to that URL instead.
    """

    def create_user_and_associated_entries(self, request, attributemap):
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=attributemap["username"],
                    first_name=attributemap["first_name"],
                    last_name=attributemap["last_name"],
                    email=attributemap["email"],
                )
                agency_instance = Agency.objects.get(pk=1)
                UserWork.objects.create(user=user, agency=agency_instance)
                UserProfile.objects.create(user=user)
                UserContact.objects.create(user=user)

                user.is_staff = True
                user.set_password(settings.EXTERNAL_PASS)
                user.save()
                return user
        except Exception as e:
            raise ParseError(str(e))
            # settings.LOGGER.error(str(e))
            # return None

    def save_request_meta_to_file(self, meta_data):
        file_path = os.path.join(settings.BASE_DIR, "requestsMeta.txt")
        print(f"WRITING UP META TO: {file_path}")
        mode = "w+"
        with open(file_path, mode) as file:
            file.write(str(meta_data) + "\n")

    def process_request(self, request):
        # Logout headers included with request.
        if (
            (
                request.path.startswith("/logout")
                or request.path.startswith("/api/v1/users/log-out")
                or request.path.startswith("/api/v1/users/logout")
                or request.path.startswith("/admin/logout")
                or request.path.startswith("/ledger/logout")
            )
            and "HTTP_X_LOGOUT_URL" in request.META
            and request.META["HTTP_X_LOGOUT_URL"]
        ):
            self.save_request_meta_to_file(request.META)
            logout(request)
            # data = {"logoutUrl": request.META["HTTP_X_LOGOUT_URL"]}
            # return HttpResponse(data, HTTP_200_OK)
            return http.HttpResponseRedirect(request.META["HTTP_X_LOGOUT_URL"])

        # Auth2 is not enabled, skip further processing.
        if (
            "HTTP_REMOTE_USER" not in request.META
            or not request.META["HTTP_REMOTE_USER"]
        ):
            # auth2 not enabled
            return

        if VERSION < (2, 0):
            user_authenticated = request.user.is_authenticated()
        else:
            user_authenticated = request.user.is_authenticated

        # Auth2 is enabled.
        # Request user is not authenticated.
        if not user_authenticated:
            attributemap = {
                "username": "HTTP_REMOTE_USER",
                "last_name": "HTTP_X_LAST_NAME",
                "first_name": "HTTP_X_FIRST_NAME",
                "email": "HTTP_X_EMAIL",
            }

            for key, value in attributemap.items():
                if value in request.META:
                    attributemap[key] = request.META[value]

            # Optional setting: projects may define accepted user email domains either as
            # a list of strings, or a single string.
            if (
                hasattr(settings, "ALLOWED_EMAIL_SUFFIXES")
                and settings.ALLOWED_EMAIL_SUFFIXES
            ):
                allowed = settings.ALLOWED_EMAIL_SUFFIXES
                if isinstance(settings.ALLOWED_EMAIL_SUFFIXES, str):
                    allowed = [settings.ALLOWED_EMAIL_SUFFIXES]
                if not any(
                    [attributemap["email"].lower().endswith(x) for x in allowed]
                ):
                    return http.HttpResponseForbidden()

            try:
                if (
                    attributemap["email"]
                    and User.objects.filter(
                        email__iexact=attributemap["email"]
                    ).exists()
                ):
                    user = User.objects.get(email__iexact=attributemap["email"])
                elif (
                    User.__name__ != "EmailUser"
                    and User.objects.filter(
                        username__iexact=attributemap["username"]
                    ).exists()
                ):
                    user = User.objects.get(username__iexact=attributemap["username"])
                else:
                    user = self.create_user_and_associated_entries(
                        request, attributemap
                    )
            except User.DoesNotExist:
                user = self.create_user_and_associated_entries(request, attributemap)

            # Set the user's details from the supplied information.
            user.__dict__.update(attributemap)
            user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"

            # Log the user in.
            login(request, user)
            return http.HttpResponseRedirect(settings.SITE_URL)

            # # Synchronize the user groups
            # if ENABLE_AUTH2_GROUPS and "HTTP_X_GROUPS" in request.META:
            #     groups = request.META["HTTP_X_GROUPS"] or None
            #     sync_usergroups(user, groups)
            #     request.session["usergroups"] = groups
