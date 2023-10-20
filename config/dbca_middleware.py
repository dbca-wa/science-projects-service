import json
from django.contrib.auth import login, logout, get_user_model
from django import http
from django.utils.deprecation import MiddlewareMixin

User = get_user_model()


class SSOLoginMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    # def process_exception(self, request, exception):
    #     return http.HttpResponse("in exception")

    def process_request(self, request):
        print("Hi")
        self.print_request_headers(request=request)
        if request.path.startswith("/logout") and "HTTP_X_LOGOUT_URL" in request.META:
            logout(request)
            return http.HttpResponseRedirect(request.META["HTTP_X_LOGOUT_URL"])
        if not request.user.is_authenticated() and "HTTP_REMOTE_USER" in request.META:
            # logger.info("User not authenticated and remote. Debug: {0}".format(settings.DEBUG))
            attributemap = {
                "username": "HTTP_REMOTE_USER",
                "last_name": "HTTP_X_LAST_NAME",
                "first_name": "HTTP_X_FIRST_NAME",
                "email": "HTTP_X_EMAIL",
            }

            for key, value in attributemap.iteritems():
                attributemap[key] = request.META[value]

            if (
                attributemap["email"]
                and User.objects.filter(
                    email__istartswith=attributemap["email"]
                ).exists()
            ):
                user = User.objects.get(email__istartswith=attributemap["email"])
            elif User.objects.filter(
                username__iexact=attributemap["username"]
            ).exists():
                user = User.objects.get(username__iexact=attributemap["username"])
            else:
                user = User()
            user.__dict__.update(attributemap)
            user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)

    # class DBCAMiddleware:
    #     def __init__(self, get_response):
    #         self.get_response = get_response

    #     def __call__(self, request):
    #         self.print_request_headers(request)

    #         if (
    #             "HTTP_REMOTE_USER" not in request.META
    #             or not request.META["HTTP_REMOTE_USER"]
    #         ):
    #             return

    #         if (
    #             request.path.startswith("/logout")
    #             and "HTTP_X_LOGOUT_URL" in request.META
    #             and request.META["HTTP_X_LOGOUT_URL"]
    #         ):
    #             logout(request)
    #             return http.HttpResponseRedirect(request.META["HTTP_X_LOGOUT_URL"])

    #         user_auth = request.user.is_authenticated
    #         if not user_auth:
    #             # Not authenticate before
    #             attributemap = {
    #                 "username": "HTTP_REMOTE_USER",
    #                 "last_name": "HTTP_X_LAST_NAME",
    #                 "first_name": "HTTP_X_FIRST_NAME",
    #                 "email": "HTTP_X_EMAIL",
    #             }

    #             for key, value in attributemap.items():
    #                 if value in request.META:
    #                     attributemap[key] = request.META[value]

    #             if (
    #                 hasattr(settings, "ALLOWED_EMAIL_SUFFIXES")
    #                 and settings.ALLOWED_EMAIL_SUFFIXES
    #             ):
    #                 allowed = settings.ALLOWED_EMAIL_SUFFIXES
    #                 if isinstance(settings.ALLOWED_EMAIL_SUFFIXES, str):
    #                     allowed = [settings.ALLOWED_EMAIL_SUFFIXES]
    #                 if not any(
    #                     [attributemap["email"].lower().endswith(x) for x in allowed]
    #                 ):
    #                     return http.HttpResponseForbidden()

    #             if (
    #                 attributemap["email"]
    #                 and User.objects.filter(email__iexact=attributemap["email"]).exists()
    #             ):
    #                 user = User.objects.filter(email__iexact=attributemap["email"])[0]
    #             elif (User.__name__ != "EmailUser") and User.objects.filter(
    #                 username__iexact=attributemap["username"]
    #             ).exists():
    #                 user = User.objects.filter(username__iexact=attributemap["username"])[0]
    #             else:
    #                 user = User()
    #             user.__dict__.update(attributemap)
    #             user.save()
    #             user.backend = "django.contrib.auth.backends.ModelBackend"
    #             login(request, user)

    #         username = request.META.get("HTTP_REMOTE_USER")
    #         first_name = request.META.get("HTTP_X_FIRST_NAME")
    #         last_name = request.META.get("HTTP_X_LAST_NAME")
    #         email = request.META.get("HTTP_X_EMAIL")

    #         if first_name and last_name and username and email:
    #             user = User.objects.filter(username=email).first()
    #             if user:
    #                 request.user = user
    #                 BaseBackend().update_last_login(None, user)
    #                 return self.get_response(request)

    #         return self.get_response(request)

    def print_request_headers(self, request):
        # Create a copy of request.META to avoid modifying the original dictionary
        meta_dict = request.META.copy()

        # Remove sensitive and unnecessary keys from the dictionary
        keys_to_remove = ["wsgi.input", "wsgi.errors"]
        for key in keys_to_remove:
            meta_dict.pop(key, None)

        # Convert the values of type 'type' to string to avoid JSON serialization error
        for key, value in meta_dict.items():
            if isinstance(value, type):
                meta_dict[key] = str(value)

        # Print the updated request headers without the 'LimitedStream' and 'TextIOWrapper' objects
        print("Request Headers:")
        print(json.dumps(meta_dict, indent=1))
