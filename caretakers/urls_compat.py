"""
Backward compatibility URLs for caretaker endpoints.
These maintain the old URL structure from adminoptions.

DEPRECATED: These URLs will be removed in 2 releases.
Use the new /api/v1/caretakers/ endpoints instead.
"""

import logging
from functools import wraps

from django.urls import path

from . import views

logger = logging.getLogger(__name__)


def log_legacy_endpoint(view_func):
    """
    Decorator to log when legacy/backward-compatible endpoints are called.
    This helps identify if frontend is still using old URLs.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        logger.warning(
            f"⚠️  LEGACY ENDPOINT CALLED: {request.path} "
            f"(method: {request.method}, user: {request.user}) "
            f"- Please update to use /api/v1/caretakers/ endpoints"
        )
        return view_func(request, *args, **kwargs)

    return wrapper


class LegacyEndpointView:
    """
    Wrapper to add logging to class-based views for legacy endpoints.
    """

    def __init__(self, view_class):
        self.view_class = view_class

    def as_view(self, **initkwargs):
        view = self.view_class.as_view(**initkwargs)
        return log_legacy_endpoint(view)


urlpatterns = [
    # Old: /api/v1/adminoptions/caretakers
    # New: /api/v1/caretakers/
    path(
        "",
        LegacyEndpointView(views.CaretakerList).as_view(),
        name="caretaker-list-compat",
    ),
    path(
        "<int:pk>",
        LegacyEndpointView(views.CaretakerDetail).as_view(),
        name="caretaker-detail-compat",
    ),
    # Old: /api/v1/adminoptions/caretakers/pending/<int:pk>
    # New: /api/v1/caretakers/tasks/<int:pk>/
    path(
        "pending/<int:pk>",
        LegacyEndpointView(views.CaretakerTasksForUser).as_view(),
        name="caretaker-tasks-compat",
    ),
    # Old: /api/v1/adminoptions/caretakers/requests
    # New: /api/v1/caretakers/requests/
    path(
        "requests",
        LegacyEndpointView(views.CaretakerRequestList).as_view(),
        name="caretaker-requests-compat",
    ),
    # Old: /api/v1/adminoptions/caretakers/adminsetcaretaker
    # New: /api/v1/caretakers/admin-set/
    path(
        "adminsetcaretaker",
        LegacyEndpointView(views.AdminSetCaretaker).as_view(),
        name="admin-set-caretaker-compat",
    ),
    # Old: /api/v1/adminoptions/caretakers/checkcaretaker
    # New: /api/v1/caretakers/check/
    path(
        "checkcaretaker",
        LegacyEndpointView(views.CheckCaretaker).as_view(),
        name="check-caretaker-compat",
    ),
]
