"""
Pytest fixtures for communications app tests
"""
import pytest
from django.contrib.auth import get_user_model

from common.tests.factories import (
    UserFactory,
    ProjectFactory,
    ProjectDocumentFactory,
)
from communications.models import ChatRoom, DirectMessage, Comment, Reaction

User = get_user_model()


@pytest.fixture
def user(db):
    """Provide a regular user"""
    return UserFactory(
        username='testuser',
        email='test@example.com',
    )


@pytest.fixture
def other_user(db):
    """Provide another user for multi-user tests"""
    return UserFactory(
        username='otheruser',
        email='other@example.com',
    )


@pytest.fixture
def superuser(db):
    """Provide a superuser"""
    return UserFactory(
        username='admin',
        email='admin@example.com',
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def project(db):
    """Provide a project"""
    return ProjectFactory()


@pytest.fixture
def project_document(db, project):
    """Provide a project document"""
    return ProjectDocumentFactory(
        project=project,
    )


@pytest.fixture
def chat_room(db, user, other_user):
    """Provide a chat room with two users"""
    room = ChatRoom.objects.create()
    room.users.add(user, other_user)
    return room


@pytest.fixture
def direct_message(db, user, chat_room):
    """Provide a direct message"""
    return DirectMessage.objects.create(
        text='Test message',
        user=user,
        chat_room=chat_room,
        ip_address='127.0.0.1',
        is_public=True,
        is_removed=False,
    )


@pytest.fixture
def comment(db, user, project_document):
    """Provide a comment"""
    return Comment.objects.create(
        user=user,
        document=project_document,
        text='Test comment',
        ip_address='127.0.0.1',
        is_public=True,
        is_removed=False,
    )


@pytest.fixture
def reaction_on_comment(db, user, comment):
    """Provide a reaction on a comment"""
    return Reaction.objects.create(
        user=user,
        comment=comment,
        reaction=Reaction.ReactionChoices.THUMBUP,
    )


@pytest.fixture
def reaction_on_message(db, user, direct_message):
    """Provide a reaction on a direct message"""
    return Reaction.objects.create(
        user=user,
        direct_message=direct_message,
        reaction=Reaction.ReactionChoices.HEART,
    )


@pytest.fixture
def user_factory():
    """Provide UserFactory for creating users"""
    return UserFactory
