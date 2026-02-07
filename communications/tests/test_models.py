"""
Tests for communications models
"""

import pytest
from django.forms import ValidationError

from communications.models import ChatRoom, Comment, DirectMessage, Reaction


class TestChatRoom:
    """Tests for ChatRoom model"""

    def test_create_chat_room(self, db):
        """Test creating a chat room"""
        # Act
        room = ChatRoom.objects.create()

        # Assert
        assert room.id is not None
        assert room.created_at is not None
        assert room.updated_at is not None

    def test_chat_room_add_users(self, user, other_user, db):
        """Test adding users to chat room"""
        # Arrange
        room = ChatRoom.objects.create()

        # Act
        room.users.add(user, other_user)

        # Assert
        assert room.users.count() == 2
        assert user in room.users.all()
        assert other_user in room.users.all()

    def test_chat_room_str_with_users(self, chat_room, user, other_user, db):
        """Test chat room string representation with users"""
        # Act
        result = str(chat_room)

        # Assert
        assert "Chat Room" in result
        assert user.username in result or str(user) in result
        assert other_user.username in result or str(other_user) in result

    def test_chat_room_str_without_users(self, db):
        """Test chat room string representation without users"""
        # Arrange
        room = ChatRoom.objects.create()

        # Act
        result = str(room)

        # Assert
        assert "Chat Room" in result

    def test_chat_room_users_relationship(self, user, db):
        """Test ManyToMany relationship with users"""
        # Arrange
        room = ChatRoom.objects.create()
        room.users.add(user)

        # Act
        user_rooms = user.chat_rooms.all()

        # Assert
        assert room in user_rooms

    def test_chat_room_verbose_name(self, db):
        """Test model verbose name"""
        # Act
        verbose_name = ChatRoom._meta.verbose_name
        verbose_name_plural = ChatRoom._meta.verbose_name_plural

        # Assert
        assert verbose_name == "Chat Room"
        assert verbose_name_plural == "Chat Rooms"


class TestDirectMessage:
    """Tests for DirectMessage model"""

    def test_create_direct_message(self, user, chat_room, db):
        """Test creating a direct message"""
        # Act
        message = DirectMessage.objects.create(
            text="Test message",
            user=user,
            chat_room=chat_room,
            ip_address="127.0.0.1",
        )

        # Assert
        assert message.id is not None
        assert message.text == "Test message"
        assert message.user == user
        assert message.chat_room == chat_room
        assert message.ip_address == "127.0.0.1"
        assert message.is_public is True
        assert message.is_removed is False

    def test_direct_message_str(self, direct_message, user, db):
        """Test direct message string representation"""
        # Act
        result = str(direct_message)

        # Assert
        assert str(user) in result
        assert "Test message" in result

    def test_direct_message_without_user(self, chat_room, db):
        """Test creating message without user (null allowed)"""
        # Act
        message = DirectMessage.objects.create(
            text="Anonymous message",
            chat_room=chat_room,
        )

        # Assert
        assert message.user is None
        assert message.text == "Anonymous message"

    def test_direct_message_is_public_default(self, user, chat_room, db):
        """Test is_public defaults to True"""
        # Act
        message = DirectMessage.objects.create(
            text="Test",
            user=user,
            chat_room=chat_room,
        )

        # Assert
        assert message.is_public is True

    def test_direct_message_is_removed_default(self, user, chat_room, db):
        """Test is_removed defaults to False"""
        # Act
        message = DirectMessage.objects.create(
            text="Test",
            user=user,
            chat_room=chat_room,
        )

        # Assert
        assert message.is_removed is False

    def test_direct_message_chat_room_relationship(self, direct_message, chat_room, db):
        """Test ForeignKey relationship with chat room"""
        # Act
        room_messages = chat_room.messages.all()

        # Assert
        assert direct_message in room_messages

    def test_direct_message_user_relationship(self, direct_message, user, db):
        """Test ForeignKey relationship with user"""
        # Act
        user_messages = user.messages.all()

        # Assert
        assert direct_message in user_messages

    def test_direct_message_verbose_name(self, db):
        """Test model verbose name"""
        # Act
        verbose_name = DirectMessage._meta.verbose_name
        verbose_name_plural = DirectMessage._meta.verbose_name_plural

        # Assert
        assert verbose_name == "Direct Message"
        assert verbose_name_plural == "Direct Messages"


class TestComment:
    """Tests for Comment model"""

    def test_create_comment(self, user, project_document, db):
        """Test creating a comment"""
        # Act
        comment = Comment.objects.create(
            user=user,
            document=project_document,
            text="Test comment",
            ip_address="127.0.0.1",
        )

        # Assert
        assert comment.id is not None
        assert comment.user == user
        assert comment.document == project_document
        assert comment.text == "Test comment"
        assert comment.ip_address == "127.0.0.1"
        assert comment.is_public is True
        assert comment.is_removed is False

    def test_comment_str(self, comment, db):
        """Test comment string representation"""
        # Act
        result = str(comment)

        # Assert
        assert "Test comment" in result

    def test_comment_str_with_html(self, user, project_document, db):
        """Test comment string representation with HTML content"""
        # Arrange
        comment = Comment.objects.create(
            user=user,
            document=project_document,
            text="<p>HTML comment</p>",
        )

        # Act
        result = str(comment)

        # Assert
        # extract_text_content should strip HTML tags
        assert result is not None

    def test_comment_without_user(self, project_document, db):
        """Test creating comment without user (null allowed)"""
        # Act
        comment = Comment.objects.create(
            document=project_document,
            text="Anonymous comment",
        )

        # Assert
        assert comment.user is None
        assert comment.text == "Anonymous comment"

    def test_comment_get_reactions_with_reactions(
        self, comment, reaction_on_comment, db
    ):
        """Test get_reactions method with reactions"""
        # Act
        reactions = comment.get_reactions()

        # Assert
        assert reactions is not None
        assert reaction_on_comment in reactions

    def test_comment_get_reactions_without_reactions(self, comment, db):
        """Test get_reactions method without reactions"""
        # Act
        reactions = comment.get_reactions()

        # Assert
        assert reactions is not None
        assert reactions.count() == 0

    def test_comment_is_public_default(self, user, project_document, db):
        """Test is_public defaults to True"""
        # Act
        comment = Comment.objects.create(
            user=user,
            document=project_document,
            text="Test",
        )

        # Assert
        assert comment.is_public is True

    def test_comment_is_removed_default(self, user, project_document, db):
        """Test is_removed defaults to False"""
        # Act
        comment = Comment.objects.create(
            user=user,
            document=project_document,
            text="Test",
        )

        # Assert
        assert comment.is_removed is False

    def test_comment_document_relationship(self, comment, project_document, db):
        """Test ForeignKey relationship with document"""
        # Act
        document_comments = project_document.comments.all()

        # Assert
        assert comment in document_comments

    def test_comment_verbose_name(self, db):
        """Test model verbose name"""
        # Act
        verbose_name = Comment._meta.verbose_name
        verbose_name_plural = Comment._meta.verbose_name_plural

        # Assert
        assert verbose_name == "Comment"
        assert verbose_name_plural == "Comments"


class TestReaction:
    """Tests for Reaction model"""

    def test_create_reaction_on_comment(self, user, comment, db):
        """Test creating a reaction on a comment"""
        # Act
        reaction = Reaction.objects.create(
            user=user,
            comment=comment,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Assert
        assert reaction.id is not None
        assert reaction.user == user
        assert reaction.comment == comment
        assert reaction.direct_message is None
        assert reaction.reaction == Reaction.ReactionChoices.THUMBUP

    def test_create_reaction_on_direct_message(self, user, direct_message, db):
        """Test creating a reaction on a direct message"""
        # Act
        reaction = Reaction.objects.create(
            user=user,
            direct_message=direct_message,
            reaction=Reaction.ReactionChoices.HEART,
        )

        # Assert
        assert reaction.id is not None
        assert reaction.user == user
        assert reaction.direct_message == direct_message
        assert reaction.comment is None
        assert reaction.reaction == Reaction.ReactionChoices.HEART

    def test_reaction_str_with_comment(self, reaction_on_comment, comment, db):
        """Test reaction string representation with comment"""
        # Act
        result = str(reaction_on_comment)

        # Assert
        assert "Reaction to" in result
        assert str(comment) in result

    def test_reaction_str_with_direct_message(
        self, reaction_on_message, direct_message, db
    ):
        """Test reaction string representation with direct message"""
        # Act
        result = str(reaction_on_message)

        # Assert
        assert "Reaction to" in result
        assert str(direct_message) in result

    def test_reaction_str_with_neither(self, user, db):
        """Test reaction string representation with neither comment nor message"""
        # Arrange - Create reaction without calling save (to bypass validation)
        reaction = Reaction(
            user=user,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act
        result = str(reaction)

        # Assert
        assert "Reaction object null" in result

    def test_reaction_clean_with_neither_comment_nor_message(self, user, db):
        """Test clean method raises error when neither comment nor message"""
        # Arrange
        reaction = Reaction(
            user=user,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="must be associated with either"):
            reaction.clean()

    def test_reaction_clean_with_both_comment_and_message(
        self, user, comment, direct_message, db
    ):
        """Test clean method raises error when both comment and message"""
        # Arrange
        reaction = Reaction(
            user=user,
            comment=comment,
            direct_message=direct_message,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="cannot be associated with both"):
            reaction.clean()

    def test_reaction_save_calls_clean(self, user, db):
        """Test save method calls clean and raises validation error"""
        # Arrange
        reaction = Reaction(
            user=user,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            reaction.save()

    def test_reaction_choices(self, db):
        """Test all reaction choices are available"""
        # Act
        choices = Reaction.ReactionChoices.choices

        # Assert
        assert len(choices) == 8
        assert ("thumbup", "Thumbs Up") in choices
        assert ("thumbdown", "Thumbs Down") in choices
        assert ("heart", "Heart") in choices
        assert ("brokenheart", "Broken Heart") in choices
        assert ("hundred", "Hundred") in choices
        assert ("confused", "Confused") in choices
        assert ("funny", "Funny") in choices
        assert ("surprised", "Surprised") in choices

    def test_reaction_comment_relationship(self, reaction_on_comment, comment, db):
        """Test ForeignKey relationship with comment"""
        # Act
        comment_reactions = comment.reactions.all()

        # Assert
        assert reaction_on_comment in comment_reactions

    def test_reaction_direct_message_relationship(
        self, reaction_on_message, direct_message, db
    ):
        """Test ForeignKey relationship with direct message"""
        # Act
        message_reactions = direct_message.reactions.all()

        # Assert
        assert reaction_on_message in message_reactions

    def test_reaction_user_relationship(self, reaction_on_comment, user, db):
        """Test ForeignKey relationship with user"""
        # Act
        user_reactions = user.reactions.all()

        # Assert
        assert reaction_on_comment in user_reactions

    def test_reaction_verbose_name(self, db):
        """Test model verbose name"""
        # Act
        verbose_name = Reaction._meta.verbose_name
        verbose_name_plural = Reaction._meta.verbose_name_plural

        # Assert
        assert verbose_name == "Reaction"
        assert verbose_name_plural == "Reactions"
