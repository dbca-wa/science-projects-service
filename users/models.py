# region IMPORTS ===================================

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from adminoptions.models import Caretaker
from common.models import CommonModel
from medias.models import UserAvatar
from rest_framework import serializers

# endregion =======================================


# region User Models ===================================


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

    display_first_name = models.CharField(
        max_length=201,  # Max length to accommodate combined first and last names
        verbose_name=("Display First Name"),
        help_text=(
            "Automatically populated display name with first name. This is to separate from OIM's SSO and displaying on the Annual Report with accents etc."
        ),
        blank=True,
        null=True,
    )

    display_last_name = models.CharField(
        max_length=201,  # Max length to accommodate combined first and last names
        verbose_name=("Display Last Name"),
        help_text=(
            "Automatically populated display name with last name. This is to separate from OIM's SSO and displaying on the Annual Report with accents etc."
        ),
        blank=True,
        null=True,
    )

    is_aec = models.BooleanField(
        default=False,
        help_text="Whether this user can act as animal ethics committee if not an admin",
    )

    def get_caretaker_data(self, current_path=None):
        """Helper method to get data about this user as a caretaker."""
        if current_path is None:
            current_path = []

        # Only prevent recursion if we're repeating the exact same path
        if self.pk in current_path:
            return None

        # Get avatar
        avatar = self.get_image()

        # Get the first related caretaker instance (if any)
        caretaker_instance = (
            self.caretaker.first()
        )  # Use `.first()` to get a specific instance
        caretaker_pk = caretaker_instance.pk if caretaker_instance else None

        return {
            "pk": self.pk,
            "caretaker_obj_id": caretaker_pk,
            "display_first_name": self.display_first_name,
            "display_last_name": self.display_last_name,
            "is_superuser": self.is_superuser,
            "email": self.email,
            "image": avatar.get("file") if avatar else None,
            "end_date": caretaker_instance.end_date if caretaker_instance else None,
        }

    def get_caretakers_recursive(self, depth=0, max_depth=12, current_path=None):
        """Get all caretakers with recursive relationships."""
        if current_path is None:
            current_path = []

        if depth >= max_depth or self.pk in current_path:
            return []

        # Add current user to the path
        new_path = current_path + [self.pk]
        caretakers = self.get_caretakers()

        return [
            {
                **caretaker.caretaker.get_caretaker_data(new_path),
                # Recursively get caretakers of this caretaker
                "caretakers": caretaker.caretaker.get_caretakers_recursive(
                    depth + 1, max_depth, new_path
                ),
            }
            for caretaker in caretakers
            if caretaker.caretaker.get_caretaker_data(new_path) is not None
        ]

    def get_caretaking_recursive(self, depth=0, max_depth=12, current_path=None):
        """Get all users being caretaken for with recursive relationships."""
        if current_path is None:
            current_path = []

        if depth >= max_depth or self.pk in current_path:
            return []

        # Add current user to the path
        new_path = current_path + [self.pk]
        caretaking = self.get_caretaking_for()
        result = []

        for caretaking_user in caretaking:
            user_data = caretaking_user.user.get_caretaker_data(new_path)
            if user_data is not None:
                # Use a new path for each branch to avoid cross-branch conflicts
                branch_path = new_path.copy()

                caretaking_chain = caretaking_user.user.get_caretaking_recursive(
                    depth + 1, max_depth, branch_path
                )

                # Use a fresh path for caretakers to avoid conflicts with caretaking chain
                caretakers_chain = caretaking_user.user.get_caretakers_recursive(
                    0, max_depth, []
                )

                result.append(
                    {
                        **user_data,
                        "caretaking_for": caretaking_chain,
                        "caretakers": caretakers_chain,
                    }
                )

        return result

    def get_caretakers(self):
        all = Caretaker.objects.filter(user=self)
        return all

    def get_caretaking_for(self):
        all = Caretaker.objects.filter(caretaker=self)
        # print(all)
        return all

    def save(self, *args, **kwargs):
        if not self.display_first_name:
            # Automatically populate display_name with first_name and last_name
            if self.first_name:
                self.display_first_name = f"{self.first_name}"

        if not self.display_last_name:
            # Automatically populate display_name with first_name and last_name
            if self.first_name:
                self.display_last_name = f"{self.last_name}"
        super().save(*args, **kwargs)

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

        # Define a custom serializer inline
        class FileOnlySerializer(serializers.ModelSerializer):
            class Meta:
                model = UserAvatar
                fields = ["file"]  # Only include the 'file' field

        # Use the custom serializer
        ser = FileOnlySerializer(avatar)
        return ser.data

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.username})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


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


class UserProfile(CommonModel):
    class TitleChoices(models.TextChoices):
        MR = "mr", "Mr"
        MS = "ms", "Ms"
        MRS = "mrs", "Mrs"
        APROF = "aprof", "A/Prof"
        PROF = "prof", "Prof"
        DR = "dr", "Dr"

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

    def __str__(self) -> str:
        return f"Profile | {self.user.username if self.user else 'No User'}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# endregion =======================================


# region Staff Profile Models ===================================


# Display underneath name and title
class KeywordTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


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

    public_profile = models.ForeignKey(
        "users.PublicStaffProfile",
        on_delete=models.CASCADE,
        related_name="education_entries",
    )
    # REMOVED UPON USER REQUEST
    # class QualificationKindChoices(models.TextChoices):
    #     POSTDOCTORAL = "postdoc", "Postdoctoral in"
    #     DOCTOR = "doc", "Doctor of"  # including philosophy (phd)
    #     # PHD = 'PhD in', 'PhD in'
    #     MASTER = "master", "Master of"
    #     GRADUATE_DIPLOMA = "graddip", "Graduate Diploma in"
    #     BACHELOR = "bachelor", "Bachelor of"
    #     ASSOCIATE_DEGREE = "assdegree", "Associate Degree in"
    #     DIPLOMA = "diploma", "Diploma in"
    #     CERTIFICATE = "cert", "Certificate in"
    #     NANODEGREE = "nano", "Nanodegree in"
    # qualification_field = models.CharField(max_length=200)
    # with_honours = models.BooleanField(default=False)
    # qualification_kind = models.CharField(
    #     max_length=50, choices=QualificationKindChoices.choices
    # )
    qualification_name = models.CharField(max_length=200)
    # start_year = models.PositiveIntegerField(blank=True, null=True)
    end_year = models.PositiveIntegerField()
    institution = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.qualification_name} from {self.institution} ({self.end_year})"


# For adding DOI publications
class DOIPublication(CommonModel):
    """Definition for Additional Publications (staff profile)"""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="doipublications",
    )
    doi = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.pk} | {self.user} | {self.doi}"

    class Meta:
        verbose_name = "DOI Publication"
        verbose_name_plural = "DOI Publications"


class PublicStaffProfile(CommonModel):
    class TitleChoices(models.TextChoices):
        MR = "mr", "Mr"
        MS = "ms", "Ms"
        MRS = "mrs", "Mrs"
        APROF = "aprof", "A/Prof"
        PROF = "prof", "Prof"
        DR = "dr", "Dr"

    it_asset_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    employee_id = models.CharField(
        max_length=50,
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
    public_email = models.EmailField(
        blank=True, null=True, help_text="Publicly displayed email address."
    )
    public_email_on = models.BooleanField(
        default=False,
        help_text="Whether to display the public email on the public profile.",
    )
    custom_title = models.CharField(
        max_length=50, blank=True, null=True, help_text="Custom title or position name."
    )
    custom_title_on = models.BooleanField(
        default=False,
        help_text="Whether to display the custom title on the public profile.",
    )

    def get_it_asset_data(self):
        it_asset_id = self.it_asset_id

        if it_asset_id:
            api_url = f"{settings.IT_ASSETS_URL}{it_asset_id}"
        else:
            api_url = settings.IT_ASSETS_URL

        response = requests.get(
            api_url,
            auth=(
                settings.IT_ASSETS_USER,
                settings.IT_ASSETS_ACCESS_TOKEN,
            ),
        )

        if response.status_code != 200:
            if settings.IT_ASSETS_USER == None:
                settings.LOGGER.warning("No IT_ASSETS_USER found in settings/env")
            if settings.IT_ASSETS_ACCESS_TOKEN == None:
                settings.LOGGER.warning(
                    "No IT_ASSETS_ACCESS_TOKEN found in settings/env"
                )
            settings.LOGGER.error(
                f"Failed to retrieve data from API:\n{response.status_code}: {response.text}"
            )
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
            api_url = f"{settings.IT_ASSETS_URL}{it_asset_id}"
        else:
            api_url = settings.IT_ASSETS_URL

        response = requests.get(
            api_url,
            auth=(
                settings.IT_ASSETS_USER,
                settings.IT_ASSETS_ACCESS_TOKEN,
            ),
        )

        if response.status_code != 200:
            if settings.IT_ASSETS_USER == None:
                settings.LOGGER.warning("No IT_ASSETS_USER found in settings/env")
            if settings.IT_ASSETS_ACCESS_TOKEN == None:
                settings.LOGGER.warning(
                    "No IT_ASSETS_ACCESS_TOKEN found in settings/env"
                )
            settings.LOGGER.error(
                f"Failed to retrieve data from API:\n{response.status_code}: {response.text}"
            )
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


# endregion =======================================
