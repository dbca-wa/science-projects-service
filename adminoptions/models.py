from django.db import models
from django.forms import ValidationError
from common.models import CommonModel


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
