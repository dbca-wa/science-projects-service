# region Imports ================================================================================================
import os, requests
import tempfile
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import login, get_user_model
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ParseError
from agencies.models import Agency
from contacts.models import UserContact
from users.models import PublicStaffProfile, UserProfile, UserWork

# endregion ====================================================================================================

User = get_user_model()


# Extended custom middleware is necessary as the base middleware only has
# specific fields available (SPMS needs to populate more tables with data on creation)
class DBCAMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def create_user_and_associated_entries(self, request, attributemap):
        try:
            with transaction.atomic():
                # Initialize IT Assets variables with defaults
                it_asset_id = None
                employee_id = None

                # Create user and basic profile entities
                user = User.objects.create_user(
                    username=attributemap["username"],
                    first_name=attributemap["first_name"],
                    last_name=attributemap["last_name"],
                    display_first_name=attributemap["first_name"],
                    display_last_name=attributemap["last_name"],
                    email=attributemap["email"],
                )
                agency_instance = Agency.objects.get(pk=1)
                UserWork.objects.create(user=user, agency=agency_instance)
                UserProfile.objects.create(user=user)
                UserContact.objects.create(user=user)
                user.is_staff = True
                user.set_password(settings.EXTERNAL_PASS)
                user.save()

                # Try to get IT Assets data, but don't fail if unavailable
                if hasattr(settings, "IT_ASSETS_URL") and settings.IT_ASSETS_URL:
                    try:
                        # Add timeout to prevent long waits
                        response = requests.get(
                            settings.IT_ASSETS_URL,
                            auth=(
                                settings.IT_ASSETS_USER or "",
                                settings.IT_ASSETS_ACCESS_TOKEN or "",
                            ),
                            timeout=5,  # 5 seconds timeout
                        )

                        if response.status_code == 200:
                            try:
                                api_data = response.json()
                                matching_record = next(
                                    (
                                        item
                                        for item in api_data
                                        if item["email"] == attributemap["email"]
                                    ),
                                    None,
                                )
                                if matching_record:
                                    it_asset_id = matching_record.get("id")
                                    employee_id = matching_record.get("employee_id")
                            except (ValueError, KeyError) as json_err:
                                settings.LOGGER.error(
                                    f"Failed to parse IT Assets response: {str(json_err)}"
                                )
                        else:
                            settings.LOGGER.warning(
                                f"IT Assets API returned status {response.status_code}"
                            )

                    except requests.exceptions.RequestException as api_err:
                        settings.LOGGER.warning(
                            f"Failed to connect to IT Assets service: {str(api_err)}"
                        )
                else:
                    settings.LOGGER.warning("IT Assets URL not configured")

                # Create PublicStaffProfile with whatever data we have (even if none)
                PublicStaffProfile.objects.create(
                    user=user,
                    is_hidden=False,
                    it_asset_id=it_asset_id,
                    employee_id=employee_id,
                )

                return user

        except Exception as e:
            settings.LOGGER.error(f"Error creating user: {str(e)}")
            raise ParseError(f"Failed to create user: {str(e)}")

    def save_request_meta_to_file(self, meta_data):
        # Create a temporary file using tempfile
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w+", suffix=".txt", dir=settings.BASE_DIR
        ) as temp_file:
            temp_file.write(str(meta_data) + "\n")
            temp_file.flush()  # Ensure data is written to the file
            temp_file_path = temp_file.name  # Store the file path for later reference

        print(f"WRITING META DATA TO TEMP FILE: {temp_file_path}")

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

            email = attributemap.get("email")
            username = attributemap.get("username")
            # Check if the user exists by email first
            user = None

            if (
                email
                and User.objects.filter(email__iexact=attributemap["email"]).exists()
            ):
                user = User.objects.filter(email__iexact=attributemap["email"]).first()

            elif username and User.objects.filter(username__iexact=username).exists():
                user = User.objects.filter(
                    username__iexact=attributemap["username"]
                ).first()
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
