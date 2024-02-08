from django.contrib import admin
from .models import (
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Affiliation,
    Division,
)


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "created_at",
        "updated_at",
    ]
    ordering = ["name"]


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
