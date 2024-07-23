from django.db import models
from common.models import CommonModel
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator, MaxValueValidator

# NOTE: I have split the photos into different models, rather than keeping them all together.
# This is to avoid empty foreign keys depending on the type of photo, and for organisational purposes.


class ProjectDocumentPDF(CommonModel):

    file = models.FileField(upload_to="project_documents/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    document = models.OneToOneField(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="pdf",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="pdfs",
    )

    def __str__(self) -> str:
        return f"PDF for {self.document.kind} - {self.project.title}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Project Document PDF"
        verbose_name_plural = "Project Document PDFs"


# DONE
class AnnualReportMedia(
    CommonModel
):  #  All media related to annual reports stored here (except pdf, which is stored seperately)
    """
    Model Images for Report Media
    """

    class MediaTypes(models.TextChoices):
        COVER = "cover", "Cover"
        REAR_COVER = "rear_cover", "Rear Cover"
        SDCHART = "sdchart", "Service Delivery Chart"
        SDCHAPTER = "service_delivery", "Service Delivery"
        RESEARCHCHAPTER = "research", "Research"
        PARTNERSHIPSCHAPTER = "partnerships", "Partnerships"
        COLLABORATIONSCHAPTER = "collaborations", "Collaborations"
        STUDENTPROJECTSCHAPTER = "student_projects", "Student Projects"
        PUBLICATIONSCHAPTER = "publications", "Publications"

    # old_file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="annual_reports/images/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    kind = models.CharField(
        max_length=140,
        choices=MediaTypes.choices,
    )
    report = models.ForeignKey(
        "documents.AnnualReport",
        on_delete=models.CASCADE,
        related_name="media",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="annual_report_media_uploaded",
    )

    def __str__(self) -> str:
        return f"({self.report.year}) {self.kind.capitalize()} Annual Report Media"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Annual Report Image"
        verbose_name_plural = "Annual Report Images"
        # Ensures there is only one kind of media per report/year (cannot have two rear covers etc.)
        constraints = [
            UniqueConstraint(
                name="unique_media_per_kind_per_year",
                fields=["kind", "report"],
            )
        ]


# This class is for uploading a PDF for older years that do not have
# an annual report w/o breaking how AnnualReportPDF works or rewriting
# code to ignore these years
class LegacyAnnualReportPDF(CommonModel):
    """
    PDF for Older Published Reports
    """

    file = models.FileField(
        upload_to="annual_reports/legacy/pdfs/", null=True, blank=True
    )
    size = models.PositiveIntegerField(default=0)  # New size field
    year = models.PositiveBigIntegerField(
        validators=[MinValueValidator(2005), MaxValueValidator(2019)]
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="legacy_annual_report_pdf_generated",
    )

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.year}) Annual Report PDF"

    class Meta:
        verbose_name = "Legacy Annual Report PDF"
        verbose_name_plural = "Legacy Annual Report PDFs"


class AnnualReportPDF(CommonModel):  #  The latest pdf for a given annual report
    """
    PDF for Report Media
    """

    # old_file = models.URLField(null=True, blank=True)
    file = models.FileField(upload_to="annual_reports/pdfs/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    report = models.OneToOneField(
        "documents.AnnualReport",
        on_delete=models.CASCADE,
        related_name="pdf",
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="annual_report_pdf_generated",
    )

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.report.year}) Annual Report PDF"

    class Meta:
        verbose_name = "Annual Report PDF"
        verbose_name_plural = "Annual Report PDFs"


class AECEndorsementPDF(CommonModel):  #  The latest pdf for a given annual report
    """
    PDF for AEC Endorsements
    """

    file = models.FileField(upload_to="aec_endorsements/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    endorsement = models.OneToOneField(
        "documents.Endorsement",
        on_delete=models.CASCADE,
        related_name="aec_pdf",
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="aec_endorsement_pdfs_uploaded",
    )

    def __str__(self) -> str:
        return f" AEC PDF ({self.endorsement})"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "AEC PDF"
        verbose_name_plural = "AEC PDFs"


# DONE
class BusinessAreaPhoto(CommonModel):
    """
    Model Definition for BusinessArea Photos
    """

    # old_file = models.URLField(null=True, blank=True)
    # file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="business_areas/", blank=True, null=True)
    size = models.PositiveIntegerField(default=0)  # New size field

    business_area = models.OneToOneField(
        "agencies.BusinessArea",
        on_delete=models.CASCADE,
        # blank=True,
        # null=True,
        related_name="image",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="business_area_photos_uploaded",
    )

    def __str__(self) -> str:
        return "Business Area Photo File"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Business Area Image"
        verbose_name_plural = "Business Area Images"


# DONE
class ProjectPhoto(CommonModel):  # Includes student projects
    """
    Model Definition for Project Photos
    """

    # old_file = models.URLField(null=True, blank=True)
    # file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="projects/", blank=True, null=True)
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        # blank=True,
        # null=True,
        related_name="image",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="project_photos_uploaded",
    )
    size = models.PositiveIntegerField(default=0)  # New size field

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return "Project Photo File"

    class Meta:
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"


class ProjectPlanMethodologyPhoto(CommonModel):  # Includes student projects
    """
    Model Definition for Project Plan Methodology Photos
    """

    file = models.ImageField(upload_to="methodology_images/", blank=True, null=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    project_plan = models.OneToOneField(
        "documents.ProjectPlan",
        on_delete=models.CASCADE,
        related_name="methodology_image",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="methodology_photos_uploaded",
    )

    def __str__(self) -> str:
        return f"Methodology Image File: {self.file}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Methodology Image File"
        verbose_name_plural = "Methodology Image Files"


#! DONE
class AgencyImage(CommonModel):
    """
    Model Definition for Agency Photos (DBCA's image)
    """

    # old_file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="agencies/")
    size = models.PositiveIntegerField(default=0)  # New size field
    agency = models.OneToOneField(
        "agencies.Agency",
        on_delete=models.CASCADE,
        # blank=True,
        # null=True,
        related_name="image",
    )

    def __str__(self) -> str:
        return "Agency Photo File"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Agency Image"
        verbose_name_plural = "Agency Images"


# DONE
class UserAvatar(CommonModel):
    """
    Model Definition for User Photos
    """

    # old_file = models.URLField(null=True, blank=True)
    # file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="user_avatars/", blank=True, null=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        # blank=True,
        # null=True,
        related_name="avatar",
    )

    def __str__(self) -> str:
        return f"User: {self.user} | {self.file.name}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User Avatar Image"
        verbose_name_plural = "User Avatar Images"


# from django.db import models
# from common.models import CommonModel
# from django.db.models import UniqueConstraint

# # NOTE: I have split the photos into different models, rather than keeping them all together.
# # This is to avoid empty foreign keys depending on the type of photo, and for organisational purposes.


# class ProjectDocumentPDF(CommonModel):
#     # old_file = models.FileField(upload_to="", null=True, blank=True)
#     file = models.FileField(upload_to="project_documents/", null=True, blank=True)
#     document = models.OneToOneField(
#         "documents.ProjectDocument",
#         on_delete=models.CASCADE,
#         related_name="pdf",
#     )
#     project = models.ForeignKey(
#         "projects.Project",
#         on_delete=models.CASCADE,
#         related_name="pdfs",
#     )

#     def __str__(self) -> str:
#         return f"PDF for {self.document.kind} - {self.project.title}"

#     class Meta:
#         verbose_name = "Project Document PDF"
#         verbose_name_plural = "Project Document PDFs"


# # DONE
# class AnnualReportMedia(
#     CommonModel
# ):  #  All media related to annual reports stored here
#     """
#     Model Definition for Report Media
#     """

#     class MediaTypes(models.TextChoices):
#         COVER = "cover", "Cover"
#         REAR_COVER = "rear_cover", "Rear Cover"
#         SDCHART = "sdchart", "Service Delivery Chart"
#         SDCHAPTER = "service_delivery", "Service Delivery"
#         RESEARCHCHAPTER = "research", "Research"
#         PARTNERSHIPSCHAPTER = "partnerships", "Partnerships"
#         COLLABORATIONSCHAPTER = "collaborations", "Collaborations"
#         STUDENTPROJECTSCHAPTER = "student_projects", "Student Projects"
#         PUBLICATIONSCHAPTER = "publications", "Publications"
#         PDF = "pdf", "PDF"

#     # old_file = models.FileField(upload_to="", null=True, blank=True)
#     file = models.FileField(upload_to="annual_reports/", null=True, blank=True)
#     kind = models.CharField(
#         max_length=140,
#         choices=MediaTypes.choices,
#     )
#     report = models.ForeignKey(
#         "documents.AnnualReport",
#         on_delete=models.CASCADE,
#         related_name="media",
#     )
#     uploader = models.ForeignKey(
#         "users.User",
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         related_name="annual_report_media_uploaded",
#     )

#     def __str__(self) -> str:
#         return f"({self.report.year}) {self.kind.capitalize()} Annual Report Media"

#     class Meta:
#         verbose_name = "Annual Report Media"
#         verbose_name_plural = "Annual Report Media"
#         # Ensures there is only one kind of media per report/year (cannot have two rear covers etc.)
#         constraints = [
#             UniqueConstraint(
#                 name="unique_media_per_kind_per_year",
#                 fields=["kind", "report"],
#             )
#         ]


# # DONE
# class BusinessAreaPhoto(CommonModel):

#     """
#     Model Definition for BusinessArea Photos
#     """

#     # old_file = models.FileField(upload_to="", null=True, blank=True)
#     file = models.FileField(upload_to="business_areas/", null=True, blank=True)
#     business_area = models.OneToOneField(
#         "agencies.BusinessArea",
#         on_delete=models.CASCADE,
#         # blank=True,
#         # null=True,
#         related_name="image",
#     )
#     uploader = models.ForeignKey(
#         "users.User",
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         related_name="business_area_photos_uploaded",
#     )

#     def __str__(self) -> str:
#         return "Business Area Photo File"

#     class Meta:
#         verbose_name = "Business Area Image"
#         verbose_name_plural = "Business Area Images"


# # DONE
# class ProjectPhoto(CommonModel):  # Includes student projects
#     """
#     Model Definition for Project Photos
#     """

#     # old_file = models.FileField(upload_to="", null=True, blank=True)
#     file = models.FileField(upload_to="projects/", null=True, blank=True)
#     project = models.OneToOneField(
#         "projects.Project",
#         on_delete=models.CASCADE,
#         # blank=True,
#         # null=True,
#         related_name="image",
#     )
#     uploader = models.ForeignKey(
#         "users.User",
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         related_name="project_photos_uploaded",
#     )

#     def __str__(self) -> str:
#         return "Project Photo File"

#     class Meta:
#         verbose_name = "Project Image"
#         verbose_name_plural = "Project Images"


# # DONE
# class AgencyImage(CommonModel):
#     """
#     Model Definition for Agency Photos (DBCA's image)
#     """

#     file = models.FileField(upload_to="agencies/", null=True, blank=True)
#     agency = models.OneToOneField(
#         "agencies.Agency",
#         on_delete=models.CASCADE,
#         # blank=True,
#         # null=True,
#         related_name="image",
#     )

#     def __str__(self) -> str:
#         return "Agency Photo File"

#     class Meta:
#         verbose_name = "Agency Image"
#         verbose_name_plural = "Agency Images"


# # DONE
# class UserAvatar(CommonModel):
#     """
#     Model Definition for User Photos
#     """

#     # old_file = models.FileField(upload_to="", null=True, blank=True)
#     file = models.FileField(upload_to="user_avatars/", null=True, blank=True)
#     user = models.ForeignKey(
#         "users.User",
#         on_delete=models.CASCADE,
#         # blank=True,
#         # null=True,
#         related_name="avatar",
#     )

#     def __str__(self) -> str:
#         return self.file

#     class Meta:
#         verbose_name = "User Avatar Image"
#         verbose_name_plural = "User Avatar Images"
