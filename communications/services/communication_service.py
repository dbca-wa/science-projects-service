"""
Communication service - Business logic for communication operations
"""

from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied

from communications.models import ChatRoom, Comment, DirectMessage, Reaction
from documents.templatetags.custom_filters import extract_text_content


class CommunicationService:
    """Business logic for communication operations"""

    # ChatRoom operations
    @staticmethod
    def list_chat_rooms():
        """List all chat rooms"""
        return ChatRoom.objects.all()

    @staticmethod
    def get_chat_room(pk):
        """Get chat room by ID"""
        try:
            return ChatRoom.objects.get(pk=pk)
        except ChatRoom.DoesNotExist:
            raise NotFound(f"Chat room {pk} not found")

    @staticmethod
    def create_chat_room(user, data):
        """Create new chat room"""
        settings.LOGGER.info(f"{user} is creating a chat room")
        return ChatRoom.objects.create(**data)

    @staticmethod
    def update_chat_room(pk, user, data):
        """Update chat room"""
        chat_room = CommunicationService.get_chat_room(pk)
        settings.LOGGER.info(f"{user} is updating a chat room {chat_room}")

        for field, value in data.items():
            setattr(chat_room, field, value)
        chat_room.save()

        return chat_room

    @staticmethod
    def delete_chat_room(pk, user):
        """Delete chat room"""
        chat_room = CommunicationService.get_chat_room(pk)
        settings.LOGGER.info(f"{user} is deleting a chat room {chat_room}")
        chat_room.delete()

    # DirectMessage operations
    @staticmethod
    def list_direct_messages():
        """List all direct messages"""
        return DirectMessage.objects.all()

    @staticmethod
    def get_direct_message(pk):
        """Get direct message by ID"""
        try:
            return DirectMessage.objects.get(pk=pk)
        except DirectMessage.DoesNotExist:
            raise NotFound(f"Direct message {pk} not found")

    @staticmethod
    def create_direct_message(user, data):
        """Create new direct message"""
        settings.LOGGER.info(f"{user} is posting a dm")
        return DirectMessage.objects.create(**data)

    @staticmethod
    def update_direct_message(pk, user, data):
        """Update direct message"""
        dm = CommunicationService.get_direct_message(pk)
        settings.LOGGER.info(f"{user} is updating a dm {dm}")

        for field, value in data.items():
            setattr(dm, field, value)
        dm.save()

        return dm

    @staticmethod
    def delete_direct_message(pk, user):
        """Delete direct message"""
        dm = CommunicationService.get_direct_message(pk)
        settings.LOGGER.info(f"{user} is deleting a dm {dm}")
        dm.delete()

    # Comment operations
    @staticmethod
    def list_comments():
        """List all comments"""
        return Comment.objects.all()

    @staticmethod
    def get_comment(pk):
        """Get comment by ID"""
        try:
            return Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            raise NotFound(f"Comment {pk} not found")

    @staticmethod
    def create_comment(user, data):
        """Create new comment"""
        settings.LOGGER.info(f"{user} is posting a comment")
        return Comment.objects.create(**data)

    @staticmethod
    def update_comment(pk, user, data):
        """Update comment"""
        comment = CommunicationService.get_comment(pk)
        settings.LOGGER.info(f"{user} is updating a comment detail {comment}")

        for field, value in data.items():
            setattr(comment, field, value)
        comment.save()

        return comment

    @staticmethod
    def delete_comment(pk, user):
        """
        Delete comment

        Raises:
            PermissionDenied: If user is not superuser or comment creator
        """
        comment = CommunicationService.get_comment(pk)

        # Block deletion by non superusers/non-creators
        if not user.is_superuser and user != comment.user:
            raise PermissionDenied("You do not have permission to delete this comment.")

        settings.LOGGER.info(
            f"{user} is deleting a comment from {comment.document}:\n{comment}"
        )
        comment.delete()

    # Reaction operations
    @staticmethod
    def list_reactions():
        """List all reactions"""
        return Reaction.objects.all()

    @staticmethod
    def get_reaction(pk):
        """Get reaction by ID"""
        try:
            return Reaction.objects.get(pk=pk)
        except Reaction.DoesNotExist:
            raise NotFound(f"Reaction {pk} not found")

    @staticmethod
    def toggle_comment_reaction(user_id, comment_id):
        """
        Toggle thumbs up reaction on a comment

        Returns:
            tuple: (reaction_object or None, was_deleted: bool)
        """
        comment = CommunicationService.get_comment(comment_id)

        # Check if reaction already exists
        existing = Reaction.objects.filter(
            user=user_id,
            reaction=Reaction.ReactionChoices.THUMBUP,
            comment=comment_id,
        ).first()

        if existing:
            settings.LOGGER.info(
                f"User {user_id} removed their reaction to:\n{extract_text_content(comment.text)}"
            )
            existing.delete()
            return None, True

        # Create new reaction
        reaction = Reaction.objects.create(
            comment=comment,
            user_id=user_id,
            reaction=Reaction.ReactionChoices.THUMBUP,
            direct_message=None,
        )

        settings.LOGGER.info(
            f"User {user_id} reacted to comment ({comment_id}):\n{extract_text_content(comment.text)}"
        )
        return reaction, False

    @staticmethod
    def update_reaction(pk, user, data):
        """Update reaction"""
        reaction = CommunicationService.get_reaction(pk)
        settings.LOGGER.info(f"{user} is updating a reaction detail {reaction}")

        for field, value in data.items():
            setattr(reaction, field, value)
        reaction.save()

        return reaction

    @staticmethod
    def delete_reaction(pk, user):
        """Delete reaction"""
        reaction = CommunicationService.get_reaction(pk)
        settings.LOGGER.info(f"{user} is deleting a reaction detail {reaction}")
        reaction.delete()
