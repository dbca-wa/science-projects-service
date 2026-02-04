"""
Tests for communication views
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from communications.models import ChatRoom, DirectMessage, Comment, Reaction

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for view tests"""
    return APIClient()


class TestChatRoomsView:
    """Tests for ChatRooms view"""

    def test_list_chat_rooms_authenticated(self, api_client, user, chat_room, db):
        """Test listing chat rooms as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/chat_rooms')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_chat_rooms_unauthenticated(self, api_client, chat_room, db):
        """Test listing chat rooms without authentication"""
        # Act
        response = api_client.get('/api/v1/communications/chat_rooms')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_chat_room_valid(self, api_client, user, db):
        """Test creating chat room with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}
        
        # Act
        response = api_client.post('/api/v1/communications/chat_rooms', data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_create_chat_room_unauthenticated(self, api_client, db):
        """Test creating chat room without authentication"""
        # Arrange
        data = {}
        
        # Act
        response = api_client.post('/api/v1/communications/chat_rooms', data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChatRoomDetailView:
    """Tests for ChatRoomDetail view"""

    def test_get_chat_room_authenticated(self, api_client, user, chat_room, db):
        """Test getting chat room detail as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/communications/chat_rooms/{chat_room.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == chat_room.id

    def test_get_chat_room_not_found(self, api_client, user, db):
        """Test getting non-existent chat room"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/chat_rooms/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_chat_room_valid(self, api_client, user, chat_room, db):
        """Test updating chat room with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}
        
        # Act
        response = api_client.put(f'/api/v1/communications/chat_rooms/{chat_room.id}', data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['id'] == chat_room.id

    def test_delete_chat_room(self, api_client, user, chat_room, db):
        """Test deleting chat room"""
        # Arrange
        api_client.force_authenticate(user=user)
        room_id = chat_room.id
        
        # Act
        response = api_client.delete(f'/api/v1/communications/chat_rooms/{room_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ChatRoom.objects.filter(id=room_id).exists()


class TestDirectMessagesView:
    """Tests for DirectMessages view"""

    def test_list_direct_messages_authenticated(self, api_client, user, direct_message, db):
        """Test listing direct messages as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/direct_messages')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_direct_messages_unauthenticated(self, api_client, direct_message, db):
        """Test listing direct messages without authentication"""
        # Act
        response = api_client.get('/api/v1/communications/direct_messages')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_direct_message_valid(self, api_client, user, chat_room, db):
        """Test creating direct message with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'text': 'New message',
            'user': user.id,
            'chat_room': chat_room.id,
            'ip_address': '192.168.1.1',
        }
        
        # Act
        response = api_client.post('/api/v1/communications/direct_messages', data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_create_direct_message_invalid(self, api_client, user, db):
        """Test creating direct message with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields
        
        # Act
        response = api_client.post('/api/v1/communications/direct_messages', data)
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDirectMessageDetailView:
    """Tests for DirectMessageDetail view"""

    def test_get_direct_message_authenticated(self, api_client, user, direct_message, db):
        """Test getting direct message detail as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/communications/direct_messages/{direct_message.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == direct_message.id
        assert response.data['text'] == 'Test message'

    def test_get_direct_message_not_found(self, api_client, user, db):
        """Test getting non-existent direct message"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/direct_messages/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_direct_message_valid(self, api_client, user, direct_message, db):
        """Test updating direct message with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {'text': 'Updated message'}
        
        # Act
        response = api_client.put(f'/api/v1/communications/direct_messages/{direct_message.id}', data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['id'] == direct_message.id

    def test_delete_direct_message(self, api_client, user, direct_message, db):
        """Test deleting direct message"""
        # Arrange
        api_client.force_authenticate(user=user)
        message_id = direct_message.id
        
        # Act
        response = api_client.delete(f'/api/v1/communications/direct_messages/{message_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not DirectMessage.objects.filter(id=message_id).exists()


class TestCommentsView:
    """Tests for Comments view"""

    def test_list_comments_authenticated(self, api_client, user, comment, db):
        """Test listing comments as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/comments')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_comments_unauthenticated(self, api_client, comment, db):
        """Test listing comments without authentication"""
        # Act
        response = api_client.get('/api/v1/communications/comments')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_comment_valid(self, api_client, user, project_document, db):
        """Test creating comment with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'user': user.id,
            'document': project_document.id,
            'text': 'New comment',
            'ip_address': '192.168.1.1',
        }
        
        # Act
        response = api_client.post('/api/v1/communications/comments', data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_create_comment_invalid(self, api_client, user, db):
        """Test creating comment with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields
        
        # Act
        response = api_client.post('/api/v1/communications/comments', data)
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCommentDetailView:
    """Tests for CommentDetail view"""

    def test_get_comment_authenticated(self, api_client, user, comment, db):
        """Test getting comment detail as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/communications/comments/{comment.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == comment.id
        assert response.data['text'] == 'Test comment'

    def test_get_comment_not_found(self, api_client, user, db):
        """Test getting non-existent comment"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/comments/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_comment_valid(self, api_client, user, comment, db):
        """Test updating comment with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {'text': 'Updated comment'}
        
        # Act
        response = api_client.put(f'/api/v1/communications/comments/{comment.id}', data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['id'] == comment.id

    def test_delete_comment_by_creator(self, api_client, user, comment, db):
        """Test deleting comment by creator"""
        # Arrange
        api_client.force_authenticate(user=user)
        comment_id = comment.id
        
        # Act
        response = api_client.delete(f'/api/v1/communications/comments/{comment_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_delete_comment_by_superuser(self, api_client, superuser, comment, db):
        """Test deleting comment by superuser"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        comment_id = comment.id
        
        # Act
        response = api_client.delete(f'/api/v1/communications/comments/{comment_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_delete_comment_permission_denied(self, api_client, other_user, comment, db):
        """Test deleting comment by non-creator raises permission denied"""
        # Arrange
        api_client.force_authenticate(user=other_user)
        
        # Act
        response = api_client.delete(f'/api/v1/communications/comments/{comment.id}')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestReactionsView:
    """Tests for Reactions view"""

    def test_list_reactions_authenticated(self, api_client, user, reaction_on_comment, db):
        """Test listing reactions as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/reactions')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_reactions_unauthenticated(self, api_client, reaction_on_comment, db):
        """Test listing reactions without authentication"""
        # Act
        response = api_client.get('/api/v1/communications/reactions')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_toggle_reaction_create(self, api_client, user, comment, db):
        """Test toggling reaction creates new reaction"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'user': user.id,
            'comment': comment.id,
        }
        
        # Act
        response = api_client.post('/api/v1/communications/reactions', data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_toggle_reaction_delete(self, api_client, user, comment, db):
        """Test toggling reaction deletes existing reaction"""
        # Arrange
        api_client.force_authenticate(user=user)
        Reaction.objects.create(
            user=user,
            comment=comment,
            reaction=Reaction.ReactionChoices.THUMBUP,
        )
        data = {
            'user': user.id,
            'comment': comment.id,
        }
        
        # Act
        response = api_client.post('/api/v1/communications/reactions', data)
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_toggle_reaction_missing_comment(self, api_client, user, db):
        """Test toggling reaction without comment ID"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {'user': user.id}
        
        # Act
        response = api_client.post('/api/v1/communications/reactions', data)
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


class TestReactionDetailView:
    """Tests for ReactionDetail view"""

    def test_get_reaction_authenticated(self, api_client, user, reaction_on_comment, db):
        """Test getting reaction detail as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/communications/reactions/{reaction_on_comment.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == reaction_on_comment.id

    def test_get_reaction_not_found(self, api_client, user, db):
        """Test getting non-existent reaction"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/communications/reactions/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_reaction_valid(self, api_client, user, reaction_on_comment, db):
        """Test updating reaction with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {'reaction': Reaction.ReactionChoices.HEART}
        
        # Act
        response = api_client.put(f'/api/v1/communications/reactions/{reaction_on_comment.id}', data)
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['id'] == reaction_on_comment.id

    def test_delete_reaction(self, api_client, user, reaction_on_comment, db):
        """Test deleting reaction"""
        # Arrange
        api_client.force_authenticate(user=user)
        reaction_id = reaction_on_comment.id
        
        # Act
        response = api_client.delete(f'/api/v1/communications/reactions/{reaction_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Reaction.objects.filter(id=reaction_id).exists()
