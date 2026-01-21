# region Imports ================================================================================================

from rest_framework.serializers import ModelSerializer

from documents.serializers import TinyProjectDocumentSerializer
from .models import (
    ChatRoom,
    Comment,
    Reaction,
    DirectMessage,
)
from users.serializers import TinyUserSerializer

# endregion ====================================================================================================


# region serializers =============================================================================================


# Direct Messages --------------------------------------------------------------------------------------------


class TinyDirectMessageSerializer(ModelSerializer):
    user = TinyUserSerializer(read_only=True)

    class Meta:
        model = DirectMessage
        fields = [
            "id",
            "text",
            "user",
            "chat_room",
        ]


class TinyReactionSerializer(ModelSerializer):
    direct_message = TinyDirectMessageSerializer()

    class Meta:
        model = Reaction
        fields = [
            "id",
            "user",
            "direct_message",
            "comment",
            "reaction",
        ]


# Comments --------------------------------------------------------------------------------------------


class TinyCommentSerializer(ModelSerializer):
    user = TinyUserSerializer(read_only=True)
    reactions = TinyReactionSerializer(many=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "document",
            "text",
            "created_at",
            "updated_at",
            "reactions",
        ]


class TinyCommentCreateSerializer(ModelSerializer):

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "document",
            "text",
            "created_at",
            "updated_at",
        ]


class CommentSerializer(ModelSerializer):
    user = TinyUserSerializer(read_only=True)
    document = TinyProjectDocumentSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = "__all__"


# Chat Rooms & Direct Messages --------------------------------------------------------------------------------------------


class TinyChatRoomSerializer(ModelSerializer):
    users = TinyUserSerializer(read_only=True, many=True)

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "users",
        ]


class DirectMessageSerializer(ModelSerializer):
    user = TinyUserSerializer(read_only=True)
    chat_room = TinyChatRoomSerializer(read_only=True)
    reactions = TinyReactionSerializer(read_only=True, many=True)

    class Meta:
        model = DirectMessage
        fields = "__all__"


class ChatRoomSerializer(ModelSerializer):
    users = TinyUserSerializer(read_only=True, many=True)
    messages = TinyDirectMessageSerializer(read_only=True, many=True)

    class Meta:
        model = ChatRoom
        fields = "__all__"


# Reactions --------------------------------------------------------------------------------------------


class ReactionSerializer(ModelSerializer):
    user = TinyUserSerializer(read_only=True)
    direct_message = TinyDirectMessageSerializer()
    comment = TinyCommentSerializer()

    class Meta:
        model = Reaction
        fields = "__all__"


class ReactionCreateSerializer(ModelSerializer):
    class Meta:
        model = Reaction
        fields = [
            "id",
            "user",
            "comment",
            "direct_message",
            "reaction",
            "created_at",
            "updated_at",
        ]


# endregion ====================================================================================================
