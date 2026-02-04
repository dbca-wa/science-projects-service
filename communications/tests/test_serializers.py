"""
Tests for communications serializers
"""
import pytest

from communications.serializers import (
    TinyDirectMessageSerializer,
    TinyReactionSerializer,
    TinyCommentSerializer,
    TinyCommentCreateSerializer,
    CommentSerializer,
    TinyChatRoomSerializer,
    DirectMessageSerializer,
    ChatRoomSerializer,
    ReactionSerializer,
    ReactionCreateSerializer,
)


class TestTinyDirectMessageSerializer:
    """Tests for TinyDirectMessageSerializer"""

    def test_serialize_direct_message(self, direct_message, db):
        """Test serializing a direct message"""
        # Act
        serializer = TinyDirectMessageSerializer(direct_message)
        data = serializer.data
        
        # Assert
        assert data['id'] == direct_message.id
        assert data['text'] == direct_message.text
        assert data['chat_room'] == direct_message.chat_room.id
        assert 'user' in data

    def test_user_field_read_only(self, direct_message, db):
        """Test user field is read-only"""
        # Arrange
        serializer = TinyDirectMessageSerializer(direct_message)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['user'].read_only is True

    def test_fields_included(self, direct_message, db):
        """Test correct fields are included"""
        # Act
        serializer = TinyDirectMessageSerializer(direct_message)
        data = serializer.data
        
        # Assert
        assert set(data.keys()) == {'id', 'text', 'user', 'chat_room'}


class TestTinyReactionSerializer:
    """Tests for TinyReactionSerializer"""

    def test_serialize_reaction_on_message(self, reaction_on_message, db):
        """Test serializing a reaction on a direct message"""
        # Act
        serializer = TinyReactionSerializer(reaction_on_message)
        data = serializer.data
        
        # Assert
        assert data['id'] == reaction_on_message.id
        assert data['user'] == reaction_on_message.user.id
        assert data['reaction'] == reaction_on_message.reaction
        assert 'direct_message' in data

    def test_serialize_reaction_on_comment(self, reaction_on_comment, db):
        """Test serializing a reaction on a comment"""
        # Act
        serializer = TinyReactionSerializer(reaction_on_comment)
        data = serializer.data
        
        # Assert
        assert data['id'] == reaction_on_comment.id
        assert data['user'] == reaction_on_comment.user.id
        assert data['comment'] == reaction_on_comment.comment.id
        assert data['reaction'] == reaction_on_comment.reaction

    def test_fields_included(self, reaction_on_comment, db):
        """Test correct fields are included"""
        # Act
        serializer = TinyReactionSerializer(reaction_on_comment)
        data = serializer.data
        
        # Assert
        assert set(data.keys()) == {'id', 'user', 'direct_message', 'comment', 'reaction'}


class TestTinyCommentSerializer:
    """Tests for TinyCommentSerializer"""

    def test_serialize_comment(self, comment, db):
        """Test serializing a comment"""
        # Act
        serializer = TinyCommentSerializer(comment)
        data = serializer.data
        
        # Assert
        assert data['id'] == comment.id
        assert data['text'] == comment.text
        assert data['document'] == comment.document.id
        assert 'user' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'reactions' in data

    def test_user_field_read_only(self, comment, db):
        """Test user field is read-only"""
        # Arrange
        serializer = TinyCommentSerializer(comment)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['user'].read_only is True

    def test_reactions_field_many(self, comment, reaction_on_comment, db):
        """Test reactions field handles multiple reactions"""
        # Act
        serializer = TinyCommentSerializer(comment)
        data = serializer.data
        
        # Assert
        assert isinstance(data['reactions'], list)
        assert len(data['reactions']) == 1

    def test_fields_included(self, comment, db):
        """Test correct fields are included"""
        # Act
        serializer = TinyCommentSerializer(comment)
        data = serializer.data
        
        # Assert
        assert set(data.keys()) == {
            'id', 'user', 'document', 'text', 
            'created_at', 'updated_at', 'reactions'
        }


class TestTinyCommentCreateSerializer:
    """Tests for TinyCommentCreateSerializer"""

    def test_serialize_comment(self, comment, db):
        """Test serializing a comment for creation"""
        # Act
        serializer = TinyCommentCreateSerializer(comment)
        data = serializer.data
        
        # Assert
        assert data['id'] == comment.id
        assert data['text'] == comment.text
        assert data['document'] == comment.document.id
        assert data['user'] == comment.user.id
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_deserialize_comment(self, user, project_document, db):
        """Test deserializing comment data"""
        # Arrange
        data = {
            'user': user.id,
            'document': project_document.id,
            'text': 'New comment',
        }
        
        # Act
        serializer = TinyCommentCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        comment = serializer.save()
        assert comment.text == 'New comment'
        assert comment.user == user
        assert comment.document == project_document

    def test_fields_included(self, comment, db):
        """Test correct fields are included"""
        # Act
        serializer = TinyCommentCreateSerializer(comment)
        data = serializer.data
        
        # Assert
        assert set(data.keys()) == {
            'id', 'user', 'document', 'text', 
            'created_at', 'updated_at'
        }


class TestCommentSerializer:
    """Tests for CommentSerializer"""

    def test_serialize_comment(self, comment, db):
        """Test serializing a comment with all fields"""
        # Act
        serializer = CommentSerializer(comment)
        data = serializer.data
        
        # Assert
        assert data['id'] == comment.id
        assert data['text'] == comment.text
        assert 'user' in data
        assert 'document' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'ip_address' in data
        assert 'is_public' in data
        assert 'is_removed' in data

    def test_user_field_read_only(self, comment, db):
        """Test user field is read-only"""
        # Arrange
        serializer = CommentSerializer(comment)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['user'].read_only is True

    def test_document_field_read_only(self, comment, db):
        """Test document field is read-only"""
        # Arrange
        serializer = CommentSerializer(comment)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['document'].read_only is True

    def test_all_fields_included(self, comment, db):
        """Test all model fields are included"""
        # Act
        serializer = CommentSerializer(comment)
        data = serializer.data
        
        # Assert
        # Should include all fields from model
        assert 'id' in data
        assert 'user' in data
        assert 'document' in data
        assert 'text' in data
        assert 'ip_address' in data
        assert 'is_public' in data
        assert 'is_removed' in data
        assert 'created_at' in data
        assert 'updated_at' in data


class TestTinyChatRoomSerializer:
    """Tests for TinyChatRoomSerializer"""

    def test_serialize_chat_room(self, chat_room, db):
        """Test serializing a chat room"""
        # Act
        serializer = TinyChatRoomSerializer(chat_room)
        data = serializer.data
        
        # Assert
        assert data['id'] == chat_room.id
        assert 'users' in data
        assert isinstance(data['users'], list)

    def test_users_field_read_only(self, chat_room, db):
        """Test users field is read-only"""
        # Arrange
        serializer = TinyChatRoomSerializer(chat_room)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['users'].read_only is True

    def test_users_field_many(self, chat_room, user, other_user, db):
        """Test users field handles multiple users"""
        # Act
        serializer = TinyChatRoomSerializer(chat_room)
        data = serializer.data
        
        # Assert
        assert len(data['users']) == 2

    def test_fields_included(self, chat_room, db):
        """Test correct fields are included"""
        # Act
        serializer = TinyChatRoomSerializer(chat_room)
        data = serializer.data
        
        # Assert
        assert set(data.keys()) == {'id', 'users'}


class TestDirectMessageSerializer:
    """Tests for DirectMessageSerializer"""

    def test_serialize_direct_message(self, direct_message, db):
        """Test serializing a direct message with all fields"""
        # Act
        serializer = DirectMessageSerializer(direct_message)
        data = serializer.data
        
        # Assert
        assert data['id'] == direct_message.id
        assert data['text'] == direct_message.text
        assert 'user' in data
        assert 'chat_room' in data
        assert 'reactions' in data
        assert 'ip_address' in data
        assert 'is_public' in data
        assert 'is_removed' in data

    def test_user_field_read_only(self, direct_message, db):
        """Test user field is read-only"""
        # Arrange
        serializer = DirectMessageSerializer(direct_message)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['user'].read_only is True

    def test_chat_room_field_read_only(self, direct_message, db):
        """Test chat_room field is read-only"""
        # Arrange
        serializer = DirectMessageSerializer(direct_message)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['chat_room'].read_only is True

    def test_reactions_field_read_only(self, direct_message, db):
        """Test reactions field is read-only"""
        # Arrange
        serializer = DirectMessageSerializer(direct_message)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['reactions'].read_only is True

    def test_all_fields_included(self, direct_message, db):
        """Test all model fields are included"""
        # Act
        serializer = DirectMessageSerializer(direct_message)
        data = serializer.data
        
        # Assert
        assert 'id' in data
        assert 'text' in data
        assert 'user' in data
        assert 'chat_room' in data
        assert 'ip_address' in data
        assert 'is_public' in data
        assert 'is_removed' in data
        assert 'reactions' in data
        assert 'created_at' in data
        assert 'updated_at' in data


class TestChatRoomSerializer:
    """Tests for ChatRoomSerializer"""

    def test_serialize_chat_room(self, chat_room, db):
        """Test serializing a chat room with all fields"""
        # Act
        serializer = ChatRoomSerializer(chat_room)
        data = serializer.data
        
        # Assert
        assert data['id'] == chat_room.id
        assert 'users' in data
        assert 'messages' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_users_field_read_only(self, chat_room, db):
        """Test users field is read-only"""
        # Arrange
        serializer = ChatRoomSerializer(chat_room)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['users'].read_only is True

    def test_messages_field_read_only(self, chat_room, db):
        """Test messages field is read-only"""
        # Arrange
        serializer = ChatRoomSerializer(chat_room)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['messages'].read_only is True

    def test_messages_field_many(self, chat_room, direct_message, db):
        """Test messages field handles multiple messages"""
        # Act
        serializer = ChatRoomSerializer(chat_room)
        data = serializer.data
        
        # Assert
        assert isinstance(data['messages'], list)
        assert len(data['messages']) == 1

    def test_all_fields_included(self, chat_room, db):
        """Test all model fields are included"""
        # Act
        serializer = ChatRoomSerializer(chat_room)
        data = serializer.data
        
        # Assert
        assert 'id' in data
        assert 'users' in data
        assert 'messages' in data
        assert 'created_at' in data
        assert 'updated_at' in data


class TestReactionSerializer:
    """Tests for ReactionSerializer"""

    def test_serialize_reaction_on_comment(self, reaction_on_comment, db):
        """Test serializing a reaction on a comment"""
        # Act
        serializer = ReactionSerializer(reaction_on_comment)
        data = serializer.data
        
        # Assert
        assert data['id'] == reaction_on_comment.id
        assert 'user' in data
        assert 'comment' in data
        assert data['reaction'] == reaction_on_comment.reaction

    def test_serialize_reaction_on_message(self, reaction_on_message, db):
        """Test serializing a reaction on a direct message"""
        # Act
        serializer = ReactionSerializer(reaction_on_message)
        data = serializer.data
        
        # Assert
        assert data['id'] == reaction_on_message.id
        assert 'user' in data
        assert 'direct_message' in data
        assert data['reaction'] == reaction_on_message.reaction

    def test_user_field_read_only(self, reaction_on_comment, db):
        """Test user field is read-only"""
        # Arrange
        serializer = ReactionSerializer(reaction_on_comment)
        
        # Act
        fields = serializer.fields
        
        # Assert
        assert fields['user'].read_only is True

    def test_all_fields_included(self, reaction_on_comment, db):
        """Test all model fields are included"""
        # Act
        serializer = ReactionSerializer(reaction_on_comment)
        data = serializer.data
        
        # Assert
        assert 'id' in data
        assert 'user' in data
        assert 'comment' in data
        assert 'direct_message' in data
        assert 'reaction' in data
        assert 'created_at' in data
        assert 'updated_at' in data


class TestReactionCreateSerializer:
    """Tests for ReactionCreateSerializer"""

    def test_serialize_reaction(self, reaction_on_comment, db):
        """Test serializing a reaction for creation"""
        # Act
        serializer = ReactionCreateSerializer(reaction_on_comment)
        data = serializer.data
        
        # Assert
        assert data['id'] == reaction_on_comment.id
        assert data['user'] == reaction_on_comment.user.id
        assert data['comment'] == reaction_on_comment.comment.id
        assert data['reaction'] == reaction_on_comment.reaction

    def test_deserialize_reaction_on_comment(self, user, comment, db):
        """Test deserializing reaction data for comment"""
        # Arrange
        data = {
            'user': user.id,
            'comment': comment.id,
            'reaction': 'thumbup',
        }
        
        # Act
        serializer = ReactionCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        reaction = serializer.save()
        assert reaction.user == user
        assert reaction.comment == comment
        assert reaction.reaction == 'thumbup'

    def test_deserialize_reaction_on_message(self, user, direct_message, db):
        """Test deserializing reaction data for direct message"""
        # Arrange
        data = {
            'user': user.id,
            'direct_message': direct_message.id,
            'reaction': 'heart',
        }
        
        # Act
        serializer = ReactionCreateSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        reaction = serializer.save()
        assert reaction.user == user
        assert reaction.direct_message == direct_message
        assert reaction.reaction == 'heart'

    def test_fields_included(self, reaction_on_comment, db):
        """Test correct fields are included"""
        # Act
        serializer = ReactionCreateSerializer(reaction_on_comment)
        data = serializer.data
        
        # Assert
        assert set(data.keys()) == {
            'id', 'user', 'comment', 'direct_message', 
            'reaction', 'created_at', 'updated_at'
        }
