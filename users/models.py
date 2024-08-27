from datetime import timezone
from tracemalloc import start
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from common.models import CommonModel
from medias.models import UserAvatar
from rest_framework.serializers import (
    ModelSerializer,
)


class TinyImageSerializer(ModelSerializer):
    class Meta:
        model = UserAvatar
        fields = ["file"]


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

    # is_biometrician = models.BooleanField(
    #     default=False,
    #     help_text="Whether this user can act as a biometrician if not an admin",
    # )

    # is_herbarium_curator = models.BooleanField(
    #     default=False,
    #     help_text="Whether this user can act as a herbarium curator if not an admin",
    # )
    display_first_name = models.CharField(
        max_length=201,  # Max length to accommodate combined first and last names
        verbose_name=("Display First Name"),
        help_text=(
            "Automatically populated display name with first name. This is to separate from OIM's SSO and displaying on the Annual Report with accents etc."
        ),
    )

    display_last_name = models.CharField(
        max_length=201,  # Max length to accommodate combined first and last names
        verbose_name=("Display Last Name"),
        help_text=(
            "Automatically populated display name with last name. This is to separate from OIM's SSO and displaying on the Annual Report with accents etc."
        ),
    )

    is_aec = models.BooleanField(
        default=False,
        help_text="Whether this user can act as animal ethics committee if not an admin",
    )

    # def save(self, *args, **kwargs):
    #     if not self.display_first_name:
    #         # Automatically populate display_name with first_name and last_name
    #         if self.first_name:
    #             self.display_first_name = f"{self.first_name}"

    #     if not self.display_last_name:
    #         # Automatically populate display_name with first_name and last_name
    #         if self.first_name:
    #             self.display_last_name = f"{self.last_name}"
    #     super().save(*args, **kwargs)

    def get_formatted_name(self):
        initials = self.profile.middle_initials
        if initials:
            initials_with_dot = "".join(
                initial[0].upper() + "." for initial in initials.split()
            )
            return f"{self.display_last_name.capitalize()}, {self.display_first_name[0]}. {initials_with_dot}"
        else:
            return (
                f"{self.display_last_name.capitalize()}, {self.display_first_name[0]}."
            )

    def get_image(self):
        try:
            avatar = UserAvatar.objects.get(user=self.pk)
        except UserAvatar.DoesNotExist:
            return None
        # if not avatar.file:
        #     return None
        # else:
        #     return avatar.file
        ser = TinyImageSerializer(avatar)
        return ser.data

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
        # MAS = "master", "Master"
        APROF = "aprof", "A/Prof"
        PROF = "prof", "Prof"
        DR = "dr", "Dr."

    user = models.OneToOneField(
        "users.User",
        # unique=True,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    image = models.OneToOneField(
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
    # about = models.TextField(
    #     null=True,
    #     blank=True,
    # )
    # expertise = models.CharField(
    #     max_length=2000,
    #     null=True,
    #     blank=True,
    # )

    def __str__(self) -> str:
        return f"Profile | {self.user.username if self.user else 'No User'}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class KeywordTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PublicStaffProfile(CommonModel):
    class TitleChoices(models.TextChoices):
        MR = "mr", "Mr."
        MS = "ms", "Ms."
        MRS = "mrs", "Mrs."
        MAS = "master", "Master"
        DR = "dr", "Dr."

    it_asset_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    is_hidden = models.BooleanField(
        default=False,
        help_text="Indicates if the profile is hidden from public view.",
    )
    aucode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="AU code for internal use.",
    )

    # Base details (Header) ===========================================
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="staff_profile",
        help_text="Linked user account for this staff profile.",
    )

    # keyword_tags = models.TextField(
    #     blank=True,
    #     null=True,
    #     help_text="Comma-separated tags describing areas of expertise.",
    # )

    keyword_tags = models.ManyToManyField(
        KeywordTag,
        related_name="staff_profiles",
        blank=True,
        help_text="Tags describing areas of expertise.",
    )

    title = models.CharField(
        choices=TitleChoices.choices,
        max_length=20,
        null=True,
        blank=True,
    )

    # # Overview section ===========================================

    about = models.TextField(
        blank=True, null=True, help_text="Short biography or personal statement."
    )
    expertise = models.TextField(
        blank=True, null=True, help_text="Areas of expertise or specializations."
    )

    def get_it_asset_data(self):
        it_asset_id = self.it_asset_id

        if it_asset_id:
            api_url = (
                f"https://itassets.dbca.wa.gov.au/api/v3/departmentuser/{it_asset_id}"
            )
        else:
            api_url = "https://itassets.dbca.wa.gov.au/api/v3/departmentuser/"

        response = requests.get(
            api_url,
            auth=(
                settings.IT_ASSETS_USER,
                settings.IT_ASSETS_ACCESS_TOKEN,
            ),
        )

        if response.status_code != 200:
            print("Failed to retrieve data from API")
            return None

        api_data = response.json()
        matching_record = next(
            (item for item in api_data if item["email"] == self.user.email), None
        )

        # Remove the email from the object
        # if matching_record:
        #     matching_record.pop("email", None)
        if matching_record:
            # Extract only the specified fields
            matching_record = {
                "id": matching_record.get("id"),
                # "email": matching_record.get("email"),
                "title": matching_record.get("title"),
                "division": matching_record.get("division"),
                "unit": matching_record.get("unit"),
                "location": matching_record.get("location"),
            }

        # also save the id if not already
        if not it_asset_id and matching_record:
            self.it_asset_id = matching_record["id"]
            self.save()

        if matching_record:
            return matching_record
        return None

    def get_it_asset_email(self):
        it_asset_id = self.it_asset_id

        if it_asset_id:
            api_url = (
                f"https://itassets.dbca.wa.gov.au/api/v3/departmentuser/{it_asset_id}"
            )
        else:
            api_url = "https://itassets.dbca.wa.gov.au/api/v3/departmentuser/"

        response = requests.get(
            api_url,
            auth=(
                settings.IT_ASSETS_USER,
                settings.IT_ASSETS_ACCESS_TOKEN,
            ),
        )

        if response.status_code != 200:
            print("Failed to retrieve data from API")
            return None

        api_data = response.json()
        matching_record = next(
            (item for item in api_data if item["email"] == self.user.email), None
        )

        # also save the id if not already
        if not it_asset_id and matching_record:
            self.it_asset_id = matching_record["id"]
            self.save()

        if matching_record:
            return matching_record["email"]
        return self.email

    def __str__(self) -> str:
        return f"Staff Profile | {f'{self.user.first_name} {self.user.last_name}' if self.user else 'No User'}"

    class Meta:
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"

    # IT ASSETS
    # dbca_position_title = models.CharField(
    #     max_length=200,
    #     help_text="Position title within DBCA.",
    #     blank=True,
    #     null=True,
    # )

    # title = (DISPLAY fk to User.UserProfile (user.profile.title) - frontend will only display it if Dr.)
    # first_name = (DISPLAY fk to User.last_name )
    # last_name = (DISPLAY fk to User.first_name )
    # branch = (DISPLAY fk to User.work.branch)

    # Projects section  ===========================================
    # (pulled directly from fk, no adjustments)
    # project_memberships = models.ManyToManyField(
    #     "projects.ProjectMember",
    #     related_name="staff_profiles",
    #     help_text="Projects associated with this staff member.",
    # )

    # CV section  ===========================================
    # employment = models.ManyToManyField(
    #     "users.EmploymentEntry",
    #     related_name="staff_profiles",
    #     help_text="Employment history for this staff member.",
    # )
    # education = models.ManyToManyField(
    #     "users.EducationEntry",
    #     related_name="staff_profiles",
    #     help_text="Educational qualifications for this staff member.",
    # )

    # REMOVED FOR NOW

    # Publications section  ===========================================

    # publications = models.ManyToManyField(
    #     "users.AdditionalPublicationEntry",
    #     related_name="staff_profiles",
    #     help_text="Publications associated with this staff member.",

    # )


# For adding employment history
class EmploymentEntry(models.Model):
    public_profile = models.ForeignKey(
        "users.PublicStaffProfile",
        on_delete=models.CASCADE,
        related_name="employment_entries",
    )
    position_title = models.CharField(max_length=200)
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(blank=True, null=True)
    section = models.CharField(max_length=200, blank=True, null=True)
    employer = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.position_title} at {self.employer} ({self.start_year}-{self.end_year})"


# For adding education details
class EducationEntry(models.Model):
    class QualificationKindChoices(models.TextChoices):
        POSTDOCTORAL = "postdoc", "Postdoctoral in"
        DOCTOR = "doc", "Doctor of"  # including philosophy (phd)
        # PHD = 'PhD in', 'PhD in'
        MASTER = "master", "Master of"
        GRADUATE_DIPLOMA = "graddip", "Graduate Diploma in"
        BACHELOR = "bachelor", "Bachelor of"
        ASSOCIATE_DEGREE = "assdegree", "Associate Degree in"
        DIPLOMA = "diploma", "Diploma in"
        CERTIFICATE = "cert", "Certificate in"
        NANODEGREE = "nano", "Nanodegree in"

    public_profile = models.ForeignKey(
        "users.PublicStaffProfile",
        on_delete=models.CASCADE,
        related_name="education_entries",
    )
    #
    qualification_field = models.CharField(max_length=200)
    with_honours = models.BooleanField(default=False)
    #
    qualification_kind = models.CharField(
        max_length=50, choices=QualificationKindChoices.choices
    )
    qualification_name = models.CharField(max_length=200)
    #
    start_year = models.PositiveIntegerField(blank=True, null=True)
    end_year = models.PositiveIntegerField()
    institution = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.qualification_kind} {self.qualification_field} from {self.institution} ({self.end_year})"


# For extra projects besides those registered in SPMS
# class StaffProfileProjectEntry(CommonModel):
#     public_profile = models.ForeignKey(
#         "users.PublicStaffProfile",
#         on_delete=models.CASCADE,
#         related_name="project_entries",
#     )
#     project_membership = models.ManyToManyField(
#         "projects.ProjectMember"
#     )  # with related project
#     flavour_text = (
#         models.TextField()
#     )  # appeal the merits of this project for your CV, otherwise use the project_membership.project.description

#     def __str__(self):
#         return f"{self.project_membership.project.title}"


# For adding any additional publications not taken from ORCID/Library
# class AdditionalPublicationEntry(models.Model):
#     public_profile = models.ForeignKey(
#         "users.PublicStaffProfile",
#         on_delete=models.CASCADE,
#         related_name="additional_publications",
#     )
#     year_published = models.PositiveIntegerField()
#     entry = models.TextField()

#     def __str__(self):
#         return f"Publication in {self.year_published}: {self.entry[:30]}..."
