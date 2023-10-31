from django.db import models
from common.models import CommonModel
from django.db.models import UniqueConstraint

# NOTE: I have split the photos into different models, rather than keeping them all together.
# This is to avoid empty foreign keys depending on the type of photo, and for organisational purposes.


class ProjectDocumentPDF(CommonModel):
    old_file = models.URLField(null=True, blank=True)
    file = models.URLField(null=True, blank=True)
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

    class Meta:
        verbose_name = "Project Document PDF"
        verbose_name_plural = "Project Document PDFs"


# DONE
class AnnualReportMedia(
    CommonModel
):  #  All media related to annual reports stored here
    """
    Model Definition for Report Media
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
        PDF = "pdf", "PDF"

    old_file = models.URLField(null=True, blank=True)
    file = models.URLField(null=True, blank=True)
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

    class Meta:
        verbose_name = "Annual Report Media"
        verbose_name_plural = "Annual Report Media"
        # Ensures there is only one kind of media per report/year (cannot have two rear covers etc.)
        constraints = [
            UniqueConstraint(
                name="unique_media_per_kind_per_year",
                fields=["kind", "report"],
            )
        ]


# DONE
class BusinessAreaPhoto(CommonModel):

    """
    Model Definition for BusinessArea Photos
    """

    # old_file = models.URLField(null=True, blank=True)
    # file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="business_areas/", blank=True, null=True)

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

    def __str__(self) -> str:
        return "Project Photo File"

    class Meta:
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"


#! DONE
class AgencyImage(CommonModel):
    """
    Model Definition for Agency Photos (DBCA's image)
    """

    # old_file = models.URLField(null=True, blank=True)
    file = models.ImageField(upload_to="agencies/")
    agency = models.OneToOneField(
        "agencies.Agency",
        on_delete=models.CASCADE,
        # blank=True,
        # null=True,
        related_name="image",
    )

    def __str__(self) -> str:
        return "Agency Photo File"

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
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        # blank=True,
        # null=True,
        related_name="avatar",
    )

    def __str__(self) -> str:
        return f"User: {self.user} | {self.file.name}"

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
