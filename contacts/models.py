# region IMPORTS ====================================================================================================
from django.db import models
from django.forms import ValidationError
from common.models import CommonModel

# endregion  =================================================================================================

# region Models ====================================================================================================


class Address(CommonModel):
    """
    Model Definition for addresses of agencies and their branches
    """

    agency = models.ForeignKey(
        "agencies.agency",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="address",
    )
    branch = models.ForeignKey(
        "agencies.Branch",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="address",
    )
    street = models.CharField(max_length=140)
    suburb = models.CharField(
        max_length=140,
        null=True,
        blank=True,
    )
    city = models.CharField(max_length=140)
    zipcode = models.IntegerField()
    state = models.CharField(max_length=140)
    country = models.CharField(max_length=140)
    pobox = models.CharField(
        null=True,
        blank=True,
    )

    # Ensures either agency or branch have values, but not both
    def clean(self):
        if self.agency is None and self.branch is None:
            raise ValidationError(
                "An address must be associated with either an agency or a branch."
            )
        if self.agency and self.branch:
            raise ValidationError(
                "An address cannot be associated with both an agency and a branch."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.street} | {self.state}"

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"


class UserContact(CommonModel):
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="contact",
    )
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    alt_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    fax = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"{self.user_id} Contact"

    class Meta:
        verbose_name = "User Contact"
        verbose_name_plural = "User Contacts"


class AgencyContact(CommonModel):
    """
    Model definition for contact details of agency
    """

    agency = models.OneToOneField(
        "agencies.agency",
        on_delete=models.CASCADE,
        related_name="contact",
    )
    email = models.EmailField(
        blank=True,
        null=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    alt_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    fax = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    address = models.ForeignKey(
        "contacts.Address",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"{self.agency.name} Contact"

    class Meta:
        verbose_name = "agency Contact"
        verbose_name_plural = "agency Contacts"


class BranchContact(CommonModel):
    """
    Model definition for contact details of agency Branch
    """

    branch = models.OneToOneField(
        "agencies.Branch",
        on_delete=models.CASCADE,
        related_name="contact",
    )
    email = models.EmailField(
        blank=True,
        null=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    alt_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    fax = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    address = models.ForeignKey(
        "contacts.Address",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"{self.branch.name} Contact"

    class Meta:
        verbose_name = "Branch Contact"
        verbose_name_plural = "Branch Contacts"


# endregion  =================================================================================================
