"""
Tests for communication services
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied

from communications.models import ChatRoom, Comment, DirectMessage, Reaction
from communications.services.communication_service import CommunicationService

User = get_user_model()


class TestChatRoomService:
    """Tests for ChatRoom service operations"""

    def test_list_chat_rooms(self, chat_room, db):
        """Test listing all chat rooms"""
        # Act
        rooms = CommunicationService.list_chat_rooms()

        # Assert
        assert rooms.count() == 1
        assert chat_room in rooms

    def test_get_chat_room(self, chat_room, db):
        """Test getting chat room by ID"""
        # Act
        room = CommunicationService.get_chat_room(chat_room.id)

        # Assert
        assert room.id == chat_room.id

    def test_get_chat_room_not_found(self, db):
        """Test getting non-existent chat room raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Chat room 999 not found"):
            CommunicationService.get_chat_room(999)

    def test_create_chat_room(self, user, db):
        """Test creating a chat room"""
        # Arrange
        data = {}

        # Act
        room = CommunicationService.create_chat_room(user, data)

        # Assert
        assert room.id is not None
        assert ChatRoom.objects.filter(id=room.id).exists()

    def test_update_chat_room(self, chat_room, user, db):
        """Test updating a chat room"""
        # Arrange
        data = {}

        # Act
        updated = CommunicationService.update_chat_room(chat_room.id, user, data)

        # Assert
        assert updated.id == chat_room.id

    def test_delete_chat_room(self, chat_room, user, db):
        """Test deleting a chat room"""
        # Arrange
        room_id = chat_room.id

        # Act
        CommunicationService.delete_chat_room(room_id, user)

        # Assert
        assert not ChatRoom.objects.filter(id=room_id).exists()


class TestDirectMessageService:
    """Tests for DirectMessage service operations"""

    def test_list_direct_messages(self, direct_message, db):
        """Test listing all direct messages"""
        # Act
        messages = CommunicationService.list_direct_messages()

        # Assert
        assert messages.count() == 1
        assert direct_message in messages

    def test_get_direct_message(self, direct_message, db):
        """Test getting direct message by ID"""
        # Act
        message = CommunicationService.get_direct_message(direct_message.id)

        # Assert
        assert message.id == direct_message.id
        assert message.text == "Test message"

    def test_get_direct_message_not_found(self, db):
        """Test getting non-existent direct message raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Direct message 999 not found"):
            CommunicationService.get_direct_message(999)

    def test_create_direct_message(self, user, chat_room, db):
        """Test creating a direct message"""
        # Arrange
        data = {
            "text": "New message",
            "user": user,
            "chat_room": chat_room,
            "ip_address": "192.168.1.1",
        }

        # Act
        message = CommunicationService.create_direct_message(user, data)

        # Assert
        assert message.id is not None
        assert message.text == "New message"
        assert message.user == user
        assert message.chat_room == chat_room

    def test_update_direct_message(self, direct_message, user, db):
        """Test updating a direct message"""
        # Arrange
        data = {"text": "Updated message"}

        # Act
        updated = CommunicationService.update_direct_message(
            direct_message.id, user, data
        )

        # Assert
        assert updated.id == direct_message.id
        assert updated.text == "Updated message"

    def test_delete_direct_message(self, direct_message, user, db):
        """Test deleting a direct message"""
        # Arrange
        message_id = direct_message.id

        # Act
        CommunicationService.delete_direct_message(message_id, user)

        # Assert
        assert not DirectMessage.objects.filter(id=message_id).exists()


class TestCommentService:
    """Tests for Comment service operations"""

    def test_list_comments(self, comment, db):
        """Test listing all comments"""
        # Act
        comments = CommunicationService.list_comments()

        # Assert
        assert comments.count() == 1
        assert comment in comments

    def test_get_comment(self, comment, db):
        """Test getting comment by ID"""
        # Act
        result = CommunicationService.get_comment(comment.id)

        # Assert
        assert result.id == comment.id
        assert result.text == "Test comment"

    def test_get_comment_not_found(self, db):
        """Test getting non-existent comment raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Comment 999 not found"):
            CommunicationService.get_comment(999)

    def test_create_comment(self, user, project_document, db):
        """Test creating a comment"""
        # Arrange
        data = {
            "user": user,
            "document": project_document,
            "text": "New comment",
            "ip_address": "192.168.1.1",
        }

        # Act
        comment = CommunicationService.create_comment(user, data)

        # Assert
        assert comment.id is not None
        assert comment.text == "New comment"
        assert comment.user == user
        assert comment.document == project_document

    def test_update_comment(self, comment, user, db):
        """Test updating a comment"""
        # Arrange
        data = {"text": "Updated comment"}

        # Act
        updated = CommunicationService.update_comment(comment.id, user, data)

        # Assert
        assert updated.id == comment.id
        assert updated.text == "Updated comment"

    def test_delete_comment_by_creator(self, comment, user, db):
        """Test deleting comment by creator"""
        # Arrange
        comment_id = comment.id

        # Act
        CommunicationService.delete_comment(comment_id, user)

        # Assert
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_delete_comment_by_superuser(self, comment, superuser, db):
        """Test deleting comment by superuser"""
        # Arrange
        comment_id = comment.id

        # Act
        CommunicationService.delete_comment(comment_id, superuser)

        # Assert
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_delete_comment_permission_denied(self, comment, other_user, db):
        """Test deleting comment by non-creator raises PermissionDenied"""
        # Act & Assert
        with pytest.raises(
            PermissionDenied, match="You do not have permission to delete this comment"
        ):
            CommunicationService.delete_comment(comment.id, other_user)


class TestReactionService:
    """Tests for Reaction service operations"""

    def test_list_reactions(self, reaction_on_comment, db):
        """Test listing all reactions"""
        # Act
        reactions = CommunicationService.list_reactions()

        # Assert
        assert reactions.count() == 1
        assert reaction_on_comment in reactions

    def test_get_reaction(self, reaction_on_comment, db):
        """Test getting reaction by ID"""
        # Act
        reaction = CommunicationService.get_reaction(reaction_on_comment.id)

        # Assert
        assert reaction.id == reaction_on_comment.id
        assert reaction.reaction == Reaction.ReactionChoices.THUMBUP

    def test_get_reaction_not_found(self, db):
        """Test getting non-existent reaction raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Reaction 999 not found"):
            CommunicationService.get_reaction(999)

    def test_toggle_comment_reaction_create(self, user, comment, db):
        """Test toggling reaction creates new reaction"""
        # Act
        reaction, was_deleted = CommunicationService.toggle_comment_reaction(
            user_id=user.id, comment_id=comment.id
        )

        # Assert
        assert was_deleted is False
        assert reaction is not None
        assert reaction.user == user
        assert reaction.comment == comment
        assert reaction.reaction == Reaction.ReactionChoices.THUMBUP

    def test_toggle_comment_reaction_delete(self, user, comment, db):
        """Test toggling reaction deletes existing reaction"""
        # Arrange - Create initial reaction
        existing = Reaction.objects.create(
            user=user,
            comment=comment,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act
        reaction, was_deleted = CommunicationService.toggle_comment_reaction(
            user_id=user.id, comment_id=comment.id
        )

        # Assert
        assert was_deleted is True
        assert reaction is None
        assert not Reaction.objects.filter(id=existing.id).exists()

    def test_update_reaction(self, reaction_on_comment, user, db):
        """Test updating a reaction"""
        # Arrange
        data = {"reaction": Reaction.ReactionChoices.HEART}

        # Act
        updated = CommunicationService.update_reaction(
            reaction_on_comment.id, user, data
        )

        # Assert
        assert updated.id == reaction_on_comment.id
        assert updated.reaction == Reaction.ReactionChoices.HEART

    def test_delete_reaction(self, reaction_on_comment, user, db):
        """Test deleting a reaction"""
        # Arrange
        reaction_id = reaction_on_comment.id

        # Act
        CommunicationService.delete_reaction(reaction_id, user)

        # Assert
        assert not Reaction.objects.filter(id=reaction_id).exists()


class TestReactionValidation:
    """Tests for Reaction model validation"""

    def test_reaction_requires_comment_or_message(self, user, db):
        """Test reaction must have either comment or direct message"""
        # Arrange
        reaction = Reaction(
            user=user,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act & Assert
        with pytest.raises(Exception):  # ValidationError
            reaction.save()

    def test_reaction_cannot_have_both(self, user, comment, direct_message, db):
        """Test reaction cannot have both comment and direct message"""
        # Arrange
        reaction = Reaction(
            user=user,
            comment=comment,
            direct_message=direct_message,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act & Assert
        with pytest.raises(Exception):  # ValidationError
            reaction.save()

    def test_reaction_on_comment_valid(self, user, comment, db):
        """Test reaction on comment is valid"""
        # Arrange
        reaction = Reaction(
            user=user,
            comment=comment,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act
        reaction.save()

        # Assert
        assert reaction.id is not None
        assert reaction.comment == comment
        assert reaction.direct_message is None

    def test_reaction_on_message_valid(self, user, direct_message, db):
        """Test reaction on direct message is valid"""
        # Arrange
        reaction = Reaction(
            user=user,
            direct_message=direct_message,
            reaction=Reaction.ReactionChoices.HEART,
        )

        # Act
        reaction.save()

        # Assert
        assert reaction.id is not None
        assert reaction.direct_message == direct_message
        assert reaction.comment is None
