from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json
from adminoptions.models import (
    AdminOptions,
    AdminTask,
    Caretaker,
    ContentField,
    GuideSection,
)


# Inline admin for content fields
class ContentFieldInline(admin.TabularInline):
    model = ContentField
    extra = 1
    fields = ("title", "field_key", "description", "order")


class JSONFieldPrettyPrintMixin:
    """Mixin to pretty-print JSON fields in the admin."""

    def pretty_print_json(self, json_field):
        """Returns a formatted HTML display of a JSON field."""
        if not json_field:
            return format_html("<pre>{}</pre>", "{}")

        try:
            # If it's already a dict, convert to string
            if isinstance(json_field, dict):
                json_str = json.dumps(json_field, indent=2)
            else:
                # Parse the JSON if it's a string
                parsed = json.loads(json_field)
                json_str = json.dumps(parsed, indent=2)

            return format_html(
                '<pre style="max-height: 300px; overflow-y: auto;">{}</pre>',
                mark_safe(json_str),
            )
        except Exception as e:
            return format_html("<pre>Error formatting JSON: {}</pre>", str(e))


@admin.register(GuideSection)
class GuideSectionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "category",
        "order",
        "is_active",
        "show_divider_after",
        "field_count",
    ]
    list_filter = ["is_active", "category", "show_divider_after"]
    search_fields = ["id", "title", "category"]
    ordering = ["order"]
    inlines = [ContentFieldInline]

    fieldsets = (
        (None, {"fields": ("id", "title", "order")}),
        (
            "Display Options",
            {"fields": ("is_active", "show_divider_after", "category")},
        ),
    )

    def field_count(self, obj):
        return obj.content_fields.count()

    field_count.short_description = "Field Count"


@admin.register(ContentField)
class ContentFieldAdmin(admin.ModelAdmin):
    list_display = ["id", "field_key", "title", "section", "order", "content_preview"]
    list_filter = ["section"]
    search_fields = ["field_key", "title", "description"]
    ordering = ["section", "order"]

    def content_preview(self, obj):
        """Show a preview of the field's content from AdminOptions guide_content"""
        try:
            admin_options = AdminOptions.objects.first()
            if not admin_options or not admin_options.guide_content:
                return "No content"

            content = admin_options.guide_content.get(obj.field_key, "")
            if not content:
                return "Empty"

            # Return the first 50 characters of the content
            preview = content[:50] + "..." if len(content) > 50 else content
            return preview
        except Exception as e:
            return f"Error: {str(e)}"

    content_preview.short_description = "Content Preview"


@admin.register(AdminOptions)
class AdminOptionsAdmin(admin.ModelAdmin, JSONFieldPrettyPrintMixin):
    list_display = [
        "email_options",
        "updated_at",
        "guide_content_count",
    ]

    readonly_fields = ["guide_content_display"]

    def guide_content_count(self, obj):
        """Show the number of entries in guide_content"""
        if not obj.guide_content:
            return 0
        return len(obj.guide_content)

    guide_content_count.short_description = "Guide Content Entries"

    def guide_content_display(self, obj):
        """Display guide_content in a formatted way"""
        return self.pretty_print_json(obj.guide_content)

    guide_content_display.short_description = "Guide Content (Formatted)"

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {"fields": ("email_options", "maintainer")}),
            (
                "Guide Content",
                {
                    "fields": ("guide_content", "guide_content_display"),
                    "description": "Dynamic guide content stored as JSON.",
                },
            ),
        ]

        # legacy fields
        fieldsets.append(
            (
                "Legacy Guide Fields",
                {
                    "fields": (
                        "guide_admin",
                        "guide_about",
                        "guide_login",
                        "guide_profile",
                        "guide_user_creation",
                        "guide_user_view",
                        "guide_project_creation",
                        "guide_project_view",
                        "guide_project_team",
                        "guide_documents",
                        "guide_report",
                    ),
                    "classes": ("collapse",),
                    "description": "Legacy fields for backward compatibility. Use the new guide content system instead.",
                },
            )
        )

        return fieldsets


@admin.register(AdminTask)
class AdminTaskAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "status",
        "action",
        "requester",
        "created_at",
        "reason",
        "project",
    ]


@admin.register(Caretaker)
class CaretakerAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "user",
        "caretaker",
        "reason",
        "end_date",
        "created_at",
    ]
