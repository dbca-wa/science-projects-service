from rest_framework.authentication import BaseAuthentication, CSRFCheck
import jwt
from django.conf import settings
from users.models import User
from rest_framework import exceptions


class JWTAuthentication(BaseAuthentication):
    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """

        def dummy_get_response(request):  # pragma: no cover
            return None

        check = CSRFCheck(dummy_get_response)
        # populates request.META['CSRF_COOKIE'], which is used in process_view()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.PermissionDenied("CSRF Failed: %s" % reason)

    def authenticate(self, req):
        # print(req.headers)
        # return None
        token = req.headers.get("Jwt")
        if not token:
            return None
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        print(decoded)
        pk = decoded.get("pk")
        if not pk:
            raise exceptions.AuthenticationFailed("Invalid token")
        try:
            user = User.objects.get(pk=pk)
            self.enforce_csrf(req)
            return (user, None)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")

        # return super().authenticate(request)
