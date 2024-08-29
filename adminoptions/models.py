# region Imports ====================================================================================================
from django.db import models
from django.forms import ValidationError
from common.models import CommonModel

# endregion  =================================================================================================

# region Models ====================================================================================================


class AdminOptions(CommonModel):
    """Model Definition for Admin Controls"""

    class EmailOptions(models.TextChoices):
        ENABLED = "enabled", "Enabled"
        ADMIN = "admin", "Admin"
        DISABLED = "disabled", "Disabled"

    email_options = models.CharField(
        max_length=50,
        choices=EmailOptions.choices,
        default=EmailOptions.DISABLED,
    )
    maintainer = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin",
    )

    # ADMIN
    guide_admin = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for admin",
    )

    # ABOUT
    guide_about = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for about",
    )

    # LOGIN
    guide_login = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for login",
    )

    # PROFILE
    guide_profile = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for profile",
    )

    # USERS
    guide_user_creation = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for user creation",
    )

    guide_user_view = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for viewing users",
    )

    # PROJECTS
    guide_project_creation = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for project creation",
    )

    guide_project_view = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for viewing projects",
    )

    # TEAM
    guide_project_team = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for project teams",
    )

    # DOCUMENTS
    guide_documents = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for project documents",
    )

    # ANNUAL REPORT
    guide_report = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for annual report",
    )

    def clean(self):
        # Ensure only one instance of AdminOptions exists
        if AdminOptions.objects.exists() and self.pk is None:
            raise ValidationError("Only one instance of AdminOptions is allowed.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return "Admin Options"

    class Meta:
        verbose_name = "Admin Controls"


# endregion  =================================================================================================
