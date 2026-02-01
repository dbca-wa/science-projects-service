# Communications App

Communication features including chat rooms, direct messages, comments, and reactions.

## Overview

Manages communication features for the Science Projects Management System including chat rooms, direct messaging, document comments, and reactions.

## Architecture

Follows layered architecture pattern:
- **views/** - HTTP request/response handling
- **services/** - Business logic
- **serializers.py** - Data serialization
- **models.py** - Database models
- **utils/** - Helper functions
- **permissions/** - Authorization logic

## Models

### ChatRoom
- Chat room for group discussions

### DirectMessage
- Private messages between users

### Comment
- Comments on documents

### Reaction
- Reactions (thumbs up) to comments and messages

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/communications/chatrooms` | GET | List chat rooms |
| `/api/v1/communications/chatrooms` | POST | Create chat room |
| `/api/v1/communications/chatrooms/<id>` | GET | Get chat room |
| `/api/v1/communications/chatrooms/<id>` | PUT | Update chat room |
| `/api/v1/communications/chatrooms/<id>` | DELETE | Delete chat room |
| `/api/v1/communications/directmessages` | GET | List direct messages |
| `/api/v1/communications/directmessages` | POST | Create direct message |
| `/api/v1/communications/directmessages/<id>` | GET | Get direct message |
| `/api/v1/communications/directmessages/<id>` | PUT | Update direct message |
| `/api/v1/communications/directmessages/<id>` | DELETE | Delete direct message |
| `/api/v1/communications/comments` | GET | List comments |
| `/api/v1/communications/comments` | POST | Create comment |
| `/api/v1/communications/comments/<id>` | GET | Get comment |
| `/api/v1/communications/comments/<id>` | PUT | Update comment |
| `/api/v1/communications/comments/<id>` | DELETE | Delete comment |
| `/api/v1/communications/reactions` | GET | List reactions |
| `/api/v1/communications/reactions` | POST | Toggle reaction |
| `/api/v1/communications/reactions/<id>` | GET | Get reaction |
| `/api/v1/communications/reactions/<id>` | PUT | Update reaction |
| `/api/v1/communications/reactions/<id>` | DELETE | Delete reaction |

## Services

### CommunicationService
- `list_chat_rooms()` - List all chat rooms
- `get_chat_room(pk)` - Get chat room by ID
- `create_chat_room(user, data)` - Create chat room
- `update_chat_room(pk, user, data)` - Update chat room
- `delete_chat_room(pk, user)` - Delete chat room
- `list_direct_messages()` - List all direct messages
- `get_direct_message(pk)` - Get direct message by ID
- `create_direct_message(user, data)` - Create direct message
- `update_direct_message(pk, user, data)` - Update direct message
- `delete_direct_message(pk, user)` - Delete direct message
- `list_comments()` - List all comments
- `get_comment(pk)` - Get comment by ID
- `create_comment(user, data)` - Create comment
- `update_comment(pk, user, data)` - Update comment
- `delete_comment(pk, user)` - Delete comment (with permission check)
- `list_reactions()` - List all reactions
- `get_reaction(pk)` - Get reaction by ID
- `toggle_comment_reaction(user_id, comment_id)` - Toggle thumbs up on comment
- `update_reaction(pk, user, data)` - Update reaction
- `delete_reaction(pk, user)` - Delete reaction

## Permissions

Comments can only be deleted by:
- The comment creator
- Superusers

## Testing

```bash
poetry run python manage.py test communications
```

## Usage

```python
from communications.services import CommunicationService

# Create comment
comment = CommunicationService.create_comment(user, {
    'text': 'Great work!',
    'document': document_id,
    'user': user_id
})

# Toggle reaction
reaction, was_deleted = CommunicationService.toggle_comment_reaction(
    user_id=user.id,
    comment_id=comment.id
)
```
