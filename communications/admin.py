# region IMPORTS ====================================================================================================
import ast

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model

from users.models import User

from .models import ChatRoom, Comment, DirectMessage, Reaction

# endregion  =================================================================================================


# region Forms ====================================================================================================


class UserFilterWidget(FilteredSelectMultiple):
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def format_value(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = ast.literal_eval(value)
        if isinstance(value, int):
            value = [str(value)]  # Convert the value to a string
        return [str(v) for v in value]  # Convert each value to a string


class ChatRoomForm(forms.ModelForm):
    User = get_user_model()
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by("first_name"),
        widget=UserFilterWidget("Users", is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.initial["users"] = list(instance.users.values_list("id", flat=True))

        self.fields["users"].queryset = User.objects.all().order_by("first_name")

    class Meta:
        model = ChatRoom
        fields = "__all__"


# endregion ====================================================================================================


# region Admin ====================================================================================================


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "__str__",
        "created_at",
        "updated_at",
    ]

    form = ChatRoomForm

    list_filter = [
        "created_at",
    ]

    search_fields = [
        "users__username",
    ]


@admin.register(Comment)
class Comment(admin.ModelAdmin):
    list_display = [
        "text",
        "user",
        "document_truncated",
        "created_at",
        "is_public",
        "is_removed",
    ]

    list_filter = [
        "is_public",
        "is_removed",
    ]

    search_fields = ["text", "user__username", "document__project"]

    @admin.display(description="Document")
    def document_truncated(self, obj):
        return (
            obj.document.__str__()[:50] + "..."
            if len(obj.document.__str__()) > 50
            else obj.document.__str__()
        )


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "chat_room",
        "text",
        "ip_address",
    ]

    list_filter = [
        "is_public",
    ]

    search_fields = [
        "text",
        "user__username",
        "ip_address",
    ]


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "comment",
        "direct_message",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "comment__text",
        "comment__document__project__title",
        "direct_message__text",
        "user__username",
    ]


# endregion ====================================================================================================
