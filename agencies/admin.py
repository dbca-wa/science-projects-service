# region IMPORTS ====================================================================================================
import os
from django.contrib import admin
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


@admin.action(description="All to TXT")
def export_all_affiliations_txt(model_admin, req, selected):
    if len(selected) != 1:
        print("PLEASE SELECT ONLY ONE")
        return
    saved_affiliations = Affiliation.objects.all()
    folder = f"{os.path.dirname(os.path.realpath(__file__))}\\affiliation_exports"
    base_name = "export"
    iteration = 1
    iteration_text = f"00{iteration}"
    file_name = f"{base_name}_{iteration_text}"
    directory = f"{folder}\\{file_name}.txt"
    print(f"DIR {os.path.exists(os.path.realpath(directory))}")
    if not os.path.exists(folder):
        os.makedirs(folder)
    while os.path.exists(os.path.realpath(directory)):
        iteration += 1
        if iteration < 10:
            iteration_text = f"00{iteration}"
        elif iteration >= 10 and iteration < 100:
            iteration_text = f"0{iteration}"
        else:
            iteration_text = {iteration}
        file_name = f"{base_name}_{iteration_text}"
        directory = f"{folder}\\{file_name}.txt"
        print(f"EXISTS: {directory}")
    try:
        with open(f"{directory}", "w+", encoding="utf-8") as quotesfile:
            for affiliation in saved_affiliations:
                name = affiliation.name
                pk = affiliation.pk
                quotesfile.write(f"{name} ({pk})\n")
        print(f"{directory}")
    except Exception as e:
        print(e)


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
