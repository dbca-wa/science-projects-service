from django import http
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.backends import ModelBackend
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import login, logout, get_user_model

User = get_user_model()


# class SSOLoginMiddleware(object):
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         return self.get_response(request)

#     # def process_exception(self, request, exception):
#     #     return http.HttpResponse("in exception")

#     def print_request_headers(self, request):
#         # Create a copy of request.META to avoid modifying the original dictionary
#         meta_dict = request.META.copy()

#         # Remove sensitive and unnecessary keys from the dictionary
#         keys_to_remove = ["wsgi.input", "wsgi.errors"]
#         for key in keys_to_remove:
#             meta_dict.pop(key, None)

#         # Convert the values of type 'type' to string to avoid JSON serialization error
#         for key, value in meta_dict.items():
#             if isinstance(value, type):
#                 meta_dict[key] = str(value)

#         # Print the updated request headers without the 'LimitedStream' and 'TextIOWrapper' objects
#         print("Request Headers:")
#         print(json.dumps(meta_dict, indent=1))


#     def process_request(self, request):
#         print("Hi")
#         self.print_request_headers(request=request)
#         if request.path.startswith("/logout") and "HTTP_X_LOGOUT_URL" in request.META:
#             logout(request)
#             return http.HttpResponseRedirect(request.META["HTTP_X_LOGOUT_URL"])
#         if not request.user.is_authenticated() and "HTTP_REMOTE_USER" in request.META:
#             username = request.META.get("HTTP_REMOTE_USER")
#             first_name = request.META.get("HTTP_X_FIRST_NAME")
#             last_name = request.META.get("HTTP_X_LAST_NAME")
#             email = request.META.get("HTTP_X_EMAIL")

#             if username and email:
#                 user, created = User.objects.get_or_create(
#                     username=username,
#                     email=email,
#                     defaults={
#                         "first_name": first_name,
#                         "last_name": last_name,
#                         "is_staff": True,  # Set is_staff to True for new users
#                     },
#                 )
#                 user.backend = "django.contrib.auth.backends.ModelBackend"
#                 login(request, user)

#         return None
#     #         username = request.META.get("HTTP_REMOTE_USER")
#     #         first_name = request.META.get("HTTP_X_FIRST_NAME")
#     #         last_name = request.META.get("HTTP_X_LAST_NAME")
#     #         email = request.META.get("HTTP_X_EMAIL")

#     #         if first_name and last_name and username and email:
#     #             user = User.objects.filter(username=email).first()
#     #             if user:
#     #                 request.user = user
#     #                 BaseBackend().update_last_login(None, user)
#     #                 return self.get_response(request)

#     #         return self.get_response(request)



class DBCAMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for header, value in request.META.items():
            if header.startswith("HTTP_"):
                print(f"{header}: {value}")


        if "HTTP_REMOTE_USER" not in request.META or not request.META["HTTP_REMOTE_USER"]:
            return self.get_response(request)

        if (
            request.path.startswith("/logout")
            and "HTTP_X_LOGOUT_URL" in request.META
            and request.META["HTTP_X_LOGOUT_URL"]
        ):
            logout(request)
            return HttpResponseRedirect(request.META["HTTP_X_LOGOUT_URL"])

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
            
            print(attributemap)

            if attributemap["email"] and User.objects.filter(email__iexact=attributemap["email"]).exists():
                user = User.objects.filter(email__iexact=attributemap["email"])[0]
            elif User.__name__ != "EmailUser" and User.objects.filter(username__iexact=attributemap["username"]).exists():
                user = User.objects.filter(username__iexact=attributemap["username"])[0]
            else:
                user = User()
            user.__dict__.update(attributemap)
            # Set is_staff to True
            user.is_staff = True
            user.save()
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
                user.save(update_fields=["last_login"])  # Update the last login field
                # user.update_last_login(None)  # Update last login for the user
                return self.get_response(request)

        return self.get_response(request)
