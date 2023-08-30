from django.contrib import admin
from .models import AgencyContact, BranchContact, UserContact, Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "street",
        "state",
        "country",
        "agency",
        "branch",
    ]

    search_fields = ["street", "branch__name"]


@admin.register(UserContact)
class UserContactAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "email",
        "phone",
    ]

    search_fields = [
        "user_id__first_name",
        "user_id__username",
    ]

    ordering = ["user__first_name"]


@admin.register(BranchContact)
class BranchContactAdmin(admin.ModelAdmin):
    list_display = [
        "branch",
        "email",
        "phone",
        "display_address",
    ]

    search_fields = [
        "branch__name",
    ]

    ordering = ["branch__name"]

    def display_address(self, obj):
        if obj.address:
            return f"{obj.address.street}"
        return None

    display_address.short_description = "Address"


@admin.register(AgencyContact)
class AgencyContactAdmin(admin.ModelAdmin):
    list_display = [
        "agency",
        "email",
        "phone",
        "address",
    ]

    search_fields = [
        "agency__name",
    ]

    ordering = ["agency__name"]
