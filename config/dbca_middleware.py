import os
from django import http
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.backends import ModelBackend
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


class DBCAMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

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

    def save_request_meta_to_file(self, meta_data):
        file_path = os.path.join(settings.BASE_DIR, "requestsMeta.txt")
        print(f"WRITING UP META TO: {file_path}")
        mode = "w+"
        with open(file_path, mode) as file:
            file.write(str(meta_data) + "\n")

    def __call__(self, request):
        if (
            "HTTP_REMOTE_USER" not in request.META
            or not request.META["HTTP_REMOTE_USER"]
        ):
            return self.get_response(request)

        # if (
        #     (
        #         request.path.startswith("/logout")
        #         or request.path.startswith("/api/v1/users/log-out")
        #         or request.path.startswith("/api/v1/users/logout")
        #     )
        #     and "HTTP_X_LOGOUT_URL" in request.META
        #     and request.META["HTTP_X_LOGOUT_URL"]
        # ):
        #     settings.LOGGER.info(msg=f"{request.user} is logging out from call")
        #     # self.save_request_meta_to_file(request.META)
        #     logout(request)
        #     data = {"logoutUrl": request.META["HTTP_X_LOGOUT_URL"]}
        #     return HttpResponse(data, HTTP_200_OK)

        user_auth = request.user.is_authenticated
        if not user_auth:
            # Not authenticated before
            attributemap = {
                "username": "HTTP_REMOTE_USER",
                "last_name": "HTTP_X_LAST_NAME",
                "first_name": "HTTP_X_FIRST_NAME",
                "email": "HTTP_X_EMAIL",
            }

            for key, value in attributemap.items():
                if value in request.META:
                    attributemap[key] = request.META[value]

            if (
                attributemap["email"]
                and User.objects.filter(email__iexact=attributemap["email"]).exists()
            ):
                user = User.objects.filter(email__iexact=attributemap["email"])[0]
            elif (
                User.__name__ != "EmailUser"
                and User.objects.filter(
                    username__iexact=attributemap["username"]
                ).exists()
            ):
                user = User.objects.filter(username__iexact=attributemap["username"])[0]
            else:
                user = self.create_user_and_associated_entries(request, attributemap)

            # user.__dict__.update(attributemap)
            # Set is_staff to True
            # user.is_staff = True
            # user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)

        username = request.META.get("HTTP_REMOTE_USER")
        first_name = request.META.get("HTTP_X_FIRST_NAME")
        last_name = request.META.get("HTTP_X_LAST_NAME")
        email = request.META.get("HTTP_X_EMAIL")

        if first_name and last_name and username and email:
            user = User.objects.filter(username=email).first()
            if user:
                request.user = user
                user.save(update_fields=["last_login"])
                return self.get_response(request)

        return self.get_response(request)
