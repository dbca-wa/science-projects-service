# region IMPORTS ====================================================================================================
import mimetypes, os, tempfile
from django.contrib import admin, messages
from django.http import FileResponse
from .models import (
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Affiliation,
    Division,
)

# endregion  =================================================================================================

# region ACTIONS ====================================================================================================


@admin.action(description="Export Affiliations to TXT")
def export_all_affiliations_txt(model_admin, req, selected):
    # Ensure only one item is selected
    if len(selected) != 1:
        model_admin.message_user(req, "Please select only one item.", messages.ERROR)
        return

    # Fetch all affiliations
    saved_affiliations = Affiliation.objects.all()

    # Create a directory in the system's temp folder for the exports
    export_folder = os.path.join(tempfile.gettempdir(), "affiliation_exports")
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    # Set the base file name and determine file iteration
    base_name = "export"
    iteration = 1
    while True:
        iteration_text = str(iteration).zfill(3)
        file_name = f"{base_name}_{iteration_text}.txt"
        file_path = os.path.join(export_folder, file_name)
        if not os.path.exists(file_path):
            break  # Found a non-existing file name
        iteration += 1

    try:
        # Write the affiliations to the file
        with open(file_path, "w+", encoding="utf-8") as txt_file:
            for affiliation in saved_affiliations:
                name = affiliation.name
                pk = affiliation.pk
                txt_file.write(f"{name} ({pk})\n")

        # Inform the user
        model_admin.message_user(
            req, f"Affiliations exported to {file_path}", messages.SUCCESS
        )

        # Use Django's FileResponse to allow downloading the file
        mime_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(open(file_path, "rb"), content_type=mime_type)
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response

    except Exception as e:
        model_admin.message_user(req, f"Error during export: {str(e)}", messages.ERROR)


# endregion  =================================================================================================

# region ADMIN ====================================================================================================


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "created_at",
        "updated_at",
    ]
    ordering = ["name"]
    actions = (export_all_affiliations_txt,)


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "key_stakeholder",
    ]

    search_fields = [
        "name",
    ]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "agency",
        "manager",
    ]

    search_fields = [
        "name",
    ]

    ordering = ["name"]


@admin.register(BusinessArea)
class BusinessAreaAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "division",
        "focus",
        "leader",
    ]

    search_fields = [
        "name",
        "focus",
        "leader",
    ]

    ordering = ["name"]


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "approver",
        "director",
    ]

    list_filter = [
        "approver",
        "director",
    ]

    search_fields = ["name"]

    ordering = ["name"]


@admin.register(DepartmentalService)
class DepartmentalServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "director",
    ]

    list_filter = [
        "director",
    ]

    search_fields = ["name"]

    ordering = ["name"]


# endregion  =================================================================================================
