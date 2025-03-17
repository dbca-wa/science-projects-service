# region Imports ====================================================================================================
from django.db import models
from common.models import CommonModel

# endregion  =================================================================================================


# region Models ====================================================================================================


class Affiliation(CommonModel):
    """Model Definition for Affiliation for external users (Previously defined on UserModel)"""

    name = models.CharField(max_length=250)

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Affiliation"
        verbose_name_plural = "Affiliations"


class Agency(CommonModel):
    """Model Definition for Agency (Previously defined on UserModel)"""

    name = models.CharField(max_length=140)
    key_stakeholder = models.ForeignKey(
        "users.User",
        # Potentially change from nullable to default superuser
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agency_stakeholder",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Agency"
        verbose_name_plural = "Agencies"


class Branch(CommonModel):  # Renamed from workcenter
    """Model Definition for Business Area (Previously Workcenter)"""

    old_id = models.IntegerField()
    agency = models.ForeignKey(
        "agencies.Agency",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=140)
    manager = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        unique_together = ("agency", "name")


class BusinessArea(CommonModel):  # Renamed from program
    """Model Definition for Business Area (Previously Program)"""

    agency = models.ForeignKey(
        "agencies.Agency",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=140)
    slug = models.SlugField(
        blank=True,
        null=True,
        help_text="A URL-sage acronym of the BA's name without whitespace",
    )
    division = models.ForeignKey(
        "agencies.Division",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="business_areas",
    )

    published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    leader = models.ForeignKey(  # Renamed from program_leader
        "users.User",
        default=1,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="business_areas_led",
    )
    # If leader sets a caretaker
    caretaker = models.ForeignKey(
        "users.User",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="business_areas_caretaker",
    )

    finance_admin = models.ForeignKey(
        "users.User",
        default=1,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="business_area_finances_handled",
    )

    data_custodian = models.ForeignKey(
        "users.User",
        default=1,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="business_area_data_handled",
    )

    cost_center = models.IntegerField(
        null=True,
        blank=True,
    )
    old_leader_id = models.IntegerField(
        null=True,
        blank=True,
    )
    old_finance_admin_id = models.IntegerField(
        null=True,
        blank=True,
    )
    old_data_custodian_id = models.IntegerField(
        null=True,
        blank=True,
    )

    old_id = models.IntegerField(blank=True, null=True)

    # NOTE SPECIES AND COMMUNITIES 1230 words (this was originally 250 words - expand further when doing lexical)
    focus = models.CharField(
        max_length=1250,
        blank=True,
        null=True,
    )

    introduction = models.TextField(
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Business Area"
        verbose_name_plural = "Business Areas"
        unique_together = ("name", "agency")


class Division(CommonModel):
    """
    Model Definition for Division
    """

    old_id = models.IntegerField()
    name = models.CharField(max_length=150)
    slug = models.SlugField(
        help_text="A URL-sage acronym of the Division's name without whitespace",
    )

    director = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="divisions_led",
        help_text="The Division's director is attributed as head of the Division in reports",
    )
    approver = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="divisions_approved",
        help_text="The Approver receives notifications about outstanding requests and has permission \
            to approve documents. The approver can be anyone in a supervisory role, including the Director.",
    )
    directorate_email_list = models.ManyToManyField(
        "users.User",
        blank=True,
        related_name="email_lists",
        help_text="Users who should receive email communications for this division",
    )

    def get_directorate_email_list(self):
        """
        Returns a list of email addresses for all users in the email list
        """
        return [
            {
                "pk": user.pk,
                "email": user.email,
                "name": f"{user.display_first_name} {user.display_last_name}",
            }
            for user in self.directorate_email_list.all()
        ]

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Department Division"
        verbose_name_plural = "Department Divisions"


class DepartmentalService(CommonModel):
    """
    Model Definition for Departmental Services
    """

    name = models.CharField(max_length=320)
    director = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="services_led",
        help_text="The Service's Director",
    )
    old_id = models.IntegerField()

    class Meta:
        verbose_name = "Departmental Service"
        verbose_name_plural = "Departmental Services"

    def __str__(self):
        return f"Dept. Service: {self.name}"


# endregion  =================================================================================================
