from datetime import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from common.models import CommonModel


# TODO: serializers, admin, views, urls
class User(AbstractUser):
    """
    Custom User Model - references old pk for migration
    """

    username = models.CharField(
        ("username"),
        unique=True,
        max_length=150,
        help_text=(
            "Required. 30 characters or fewer. Letters, digits and " "@/./+/-/_ only."
        ),
    )
    first_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=("First Name"),
        help_text=("First name or given name."),
    )
    last_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=("Last Name"),
        help_text=("Last name or surname."),
    )
    email = models.EmailField(
        ("email address"),
        null=True,
        blank=True,
        unique=True,
    )

    old_pk = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Old Primary Key",
        help_text="The primary key used in the outdated SPMS",
    )

    def get_formatted_name(self):
        initials = self.profile.middle_initials
        if initials:
            initials_with_dot = "".join(
                initial[0].upper() + "." for initial in initials.split()
            )
            return f"{self.last_name.capitalize()}, {self.first_name[0]}. {initials_with_dot}"
        else:
            return f"{self.last_name.capitalize()}, {self.first_name[0]}."

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.username})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


# TODO: admin, views, urls
class UserWork(CommonModel):
    class RoleChoices(models.TextChoices):
        ECODEV = "Ecoinformatics Developer", "Ecoinformatics Developer"
        EXECDIR = "Executive Director", "Executive Director"
        ASSEXECDIR = "Assistant Executive Director", "Assistant Executive Director"
        BALEAD = "Business Area Leader", "Business Area Leader"
        ADMIN = "Admin", "Admin"
        DBCA = "DBCA Member", "DBCA Member"
        NONE = "None", "None"

    user = models.OneToOneField(
        "users.User",
        unique=True,
        on_delete=models.CASCADE,
        related_name="work",
    )
    agency = models.ForeignKey(
        "agencies.Agency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Previously work_center_id
    branch = models.ForeignKey(
        "agencies.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Previously program_id
    business_area = models.ForeignKey(
        "agencies.BusinessArea",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    affiliation = models.ForeignKey(
        "agencies.Affiliation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        default=RoleChoices.NONE,
    )

    def __str__(self) -> str:
        return f"Work Detail | {self.user}"

    class Meta:
        verbose_name = "User Work Detail"
        verbose_name_plural = "User Work Details"


# TODO: admin, views, urls
class UserProfile(CommonModel):
    class TitleChoices(models.TextChoices):
        MR = "mr", "Mr."
        MS = "ms", "Ms."
        MRS = "mrs", "Mrs."
        MAS = "master", "Master"
        DR = "dr", "Dr."

    user = models.OneToOneField(
        "users.User",
        # unique=True,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    image = models.ForeignKey(
        "medias.UserAvatar",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    title = models.CharField(
        choices=TitleChoices.choices,
        max_length=20,
        null=True,
        blank=True,
    )
    middle_initials = models.CharField(
        max_length=10,
        null=True,
        blank=True,
    )
    about = models.TextField(
        null=True,
        blank=True,
    )
    curriculum_vitae = models.TextField(
        null=True,
        blank=True,
    )
    expertise = models.CharField(
        max_length=140,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"Profile | {self.user.username if self.user else 'No User'}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
