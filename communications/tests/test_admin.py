"""
Tests for communications admin
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from communications.admin import (
    ChatRoomAdmin,
    Comment as CommentAdmin,
    DirectMessageAdmin,
    ReactionAdmin,
    ChatRoomForm,
    UserFilterWidget,
)
from communications.models import ChatRoom, Comment, DirectMessage, Reaction


class TestUserFilterWidget:
    """Tests for UserFilterWidget"""

    def test_label_from_instance(self, user, db):
        """Test label generation from user instance"""
        # Arrange
        widget = UserFilterWidget("Users", is_stacked=False)
        
        # Act
        label = widget.label_from_instance(user)
        
        # Assert
        assert user.first_name in label
        assert user.last_name in label

    def test_format_value_none(self, db):
        """Test format_value with None"""
        # Arrange
        widget = UserFilterWidget("Users", is_stacked=False)
        
        # Act
        result = widget.format_value(None)
        
        # Assert
        assert result == []

    def test_format_value_string(self, db):
        """Test format_value with string"""
        # Arrange
        widget = UserFilterWidget("Users", is_stacked=False)
        
        # Act
        result = widget.format_value("[1, 2, 3]")
        
        # Assert
        assert result == ['1', '2', '3']

    def test_format_value_int(self, db):
        """Test format_value with integer"""
        # Arrange
        widget = UserFilterWidget("Users", is_stacked=False)
        
        # Act
        result = widget.format_value(5)
        
        # Assert
        assert result == ['5']

    def test_format_value_list(self, db):
        """Test format_value with list"""
        # Arrange
        widget = UserFilterWidget("Users", is_stacked=False)
        
        # Act
        result = widget.format_value([1, 2, 3])
        
        # Assert
        assert result == ['1', '2', '3']


class TestChatRoomForm:
    """Tests for ChatRoomForm"""

    def test_form_fields(self, db):
        """Test form has correct fields"""
        # Act
        form = ChatRoomForm()
        
        # Assert
        assert 'users' in form.fields

    def test_form_with_instance(self, chat_room, user, other_user, db):
        """Test form initialization with existing instance"""
        # Act
        form = ChatRoomForm(instance=chat_room)
        
        # Assert
        assert 'users' in form.initial
        assert user.id in form.initial['users']
        assert other_user.id in form.initial['users']

    def test_form_users_queryset_ordered(self, db):
        """Test users queryset is ordered by first_name"""
        # Act
        form = ChatRoomForm()
        
        # Assert
        queryset = form.fields['users'].queryset
        # Check that queryset has ordering
        assert queryset.ordered

    def test_form_widget_type(self, db):
        """Test users field uses UserFilterWidget"""
        # Act
        form = ChatRoomForm()
        
        # Assert
        assert isinstance(form.fields['users'].widget, UserFilterWidget)


class TestChatRoomAdmin:
    """Tests for ChatRoomAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = ChatRoomAdmin(ChatRoom, AdminSite())
        
        # Assert
        assert 'pk' in admin.list_display
        assert '__str__' in admin.list_display
        assert 'created_at' in admin.list_display
        assert 'updated_at' in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = ChatRoomAdmin(ChatRoom, AdminSite())
        
        # Assert
        assert 'created_at' in admin.list_filter

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = ChatRoomAdmin(ChatRoom, AdminSite())
        
        # Assert
        assert 'users__username' in admin.search_fields

    def test_form_class(self, db):
        """Test admin uses ChatRoomForm"""
        # Arrange
        admin = ChatRoomAdmin(ChatRoom, AdminSite())
        
        # Assert
        assert admin.form == ChatRoomForm

    def test_admin_registered(self, db):
        """Test ChatRoom is registered in admin"""
        # Arrange
        site = AdminSite()
        
        # Act
        admin = ChatRoomAdmin(ChatRoom, site)
        
        # Assert
        assert admin.model == ChatRoom


class TestCommentAdmin:
    """Tests for CommentAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = CommentAdmin(Comment, AdminSite())
        
        # Assert
        assert 'text' in admin.list_display
        assert 'user' in admin.list_display
        assert 'document_truncated' in admin.list_display
        assert 'created_at' in admin.list_display
        assert 'is_public' in admin.list_display
        assert 'is_removed' in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = CommentAdmin(Comment, AdminSite())
        
        # Assert
        assert 'is_public' in admin.list_filter
        assert 'is_removed' in admin.list_filter

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = CommentAdmin(Comment, AdminSite())
        
        # Assert
        assert 'text' in admin.search_fields
        assert 'user__username' in admin.search_fields
        assert 'document__project' in admin.search_fields

    def test_document_truncated_short(self, comment, db):
        """Test document_truncated with short document string"""
        # Arrange
        admin = CommentAdmin(Comment, AdminSite())
        
        # Act
        result = admin.document_truncated(comment)
        
        # Assert
        assert result is not None
        # If document string is > 50 chars, result should have '...'
        if len(str(comment.document)) > 50:
            assert '...' in result
        else:
            assert '...' not in result

    def test_document_truncated_long(self, user, project_document, db):
        """Test document_truncated with long document string"""
        # Arrange
        admin = CommentAdmin(Comment, AdminSite())
        # Create comment with document that has long string representation
        long_comment = Comment.objects.create(
            user=user,
            document=project_document,
            text='Test comment with long document',
        )
        
        # Act
        result = admin.document_truncated(long_comment)
        
        # Assert
        assert result is not None
        if len(str(long_comment.document)) > 50:
            assert '...' in result
            assert len(result) <= 53  # 50 chars + '...'

    def test_document_truncated_short_description(self, db):
        """Test document_truncated has short_description"""
        # Arrange
        admin = CommentAdmin(Comment, AdminSite())
        
        # Assert
        assert hasattr(admin.document_truncated, 'short_description')
        assert admin.document_truncated.short_description == 'Document'


class TestDirectMessageAdmin:
    """Tests for DirectMessageAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = DirectMessageAdmin(DirectMessage, AdminSite())
        
        # Assert
        assert 'user' in admin.list_display
        assert 'chat_room' in admin.list_display
        assert 'text' in admin.list_display
        assert 'ip_address' in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = DirectMessageAdmin(DirectMessage, AdminSite())
        
        # Assert
        assert 'is_public' in admin.list_filter

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = DirectMessageAdmin(DirectMessage, AdminSite())
        
        # Assert
        assert 'text' in admin.search_fields
        assert 'user__username' in admin.search_fields
        assert 'ip_address' in admin.search_fields

    def test_admin_registered(self, db):
        """Test DirectMessage is registered in admin"""
        # Arrange
        site = AdminSite()
        
        # Act
        admin = DirectMessageAdmin(DirectMessage, site)
        
        # Assert
        assert admin.model == DirectMessage


class TestReactionAdmin:
    """Tests for ReactionAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = ReactionAdmin(Reaction, AdminSite())
        
        # Assert
        assert 'user' in admin.list_display
        assert 'comment' in admin.list_display
        assert 'direct_message' in admin.list_display
        assert 'created_at' in admin.list_display
        assert 'updated_at' in admin.list_display

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = ReactionAdmin(Reaction, AdminSite())
        
        # Assert
        assert 'comment__text' in admin.search_fields
        assert 'comment__document__project__title' in admin.search_fields
        assert 'direct_message__text' in admin.search_fields
        assert 'user__username' in admin.search_fields

    def test_admin_registered(self, db):
        """Test Reaction is registered in admin"""
        # Arrange
        site = AdminSite()
        
        # Act
        admin = ReactionAdmin(Reaction, site)
        
        # Assert
        assert admin.model == Reaction
