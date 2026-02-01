"""
Communication CRUD views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)

from communications.services import CommunicationService
from communications.serializers import (
    ChatRoomSerializer,
    TinyChatRoomSerializer,
    DirectMessageSerializer,
    TinyDirectMessageSerializer,
    CommentSerializer,
    TinyCommentSerializer,
    ReactionSerializer,
    TinyReactionSerializer,
    ReactionCreateSerializer,
)


class ChatRooms(APIView):
    """List and create chat rooms"""

    def get(self, request):
        """List all chat rooms"""
        chat_rooms = CommunicationService.list_chat_rooms()
        serializer = TinyChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new chat room"""
        serializer = ChatRoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        chat_room = CommunicationService.create_chat_room(request.user, serializer.validated_data)
        result = TinyChatRoomSerializer(chat_room)
        return Response(result.data, status=HTTP_201_CREATED)


class ChatRoomDetail(APIView):
    """Get, update, and delete chat room"""

    def get(self, request, pk):
        """Get chat room detail"""
        chat_room = CommunicationService.get_chat_room(pk)
        serializer = ChatRoomSerializer(chat_room)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update chat room"""
        serializer = ChatRoomSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        chat_room = CommunicationService.update_chat_room(pk, request.user, serializer.validated_data)
        result = TinyChatRoomSerializer(chat_room)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete chat room"""
        CommunicationService.delete_chat_room(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class DirectMessages(APIView):
    """List and create direct messages"""

    def get(self, request):
        """List all direct messages"""
        messages = CommunicationService.list_direct_messages()
        serializer = TinyDirectMessageSerializer(messages, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new direct message"""
        serializer = DirectMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        message = CommunicationService.create_direct_message(request.user, serializer.validated_data)
        result = TinyDirectMessageSerializer(message)
        return Response(result.data, status=HTTP_201_CREATED)


class DirectMessageDetail(APIView):
    """Get, update, and delete direct message"""

    def get(self, request, pk):
        """Get direct message detail"""
        message = CommunicationService.get_direct_message(pk)
        serializer = DirectMessageSerializer(message)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update direct message"""
        serializer = DirectMessageSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        message = CommunicationService.update_direct_message(pk, request.user, serializer.validated_data)
        result = TinyDirectMessageSerializer(message)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete direct message"""
        CommunicationService.delete_direct_message(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class Comments(APIView):
    """List and create comments"""

    def get(self, request):
        """List all comments"""
        comments = CommunicationService.list_comments()
        serializer = TinyCommentSerializer(comments, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new comment"""
        serializer = CommentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        comment = CommunicationService.create_comment(request.user, serializer.validated_data)
        result = TinyCommentSerializer(comment)
        return Response(result.data, status=HTTP_201_CREATED)


class CommentDetail(APIView):
    """Get, update, and delete comment"""

    def get(self, request, pk):
        """Get comment detail"""
        comment = CommunicationService.get_comment(pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update comment"""
        serializer = CommentSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        comment = CommunicationService.update_comment(pk, request.user, serializer.validated_data)
        result = TinyCommentSerializer(comment)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete comment"""
        try:
            CommunicationService.delete_comment(pk, request.user)
            return Response(status=HTTP_204_NO_CONTENT)
        except PermissionError as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_403_FORBIDDEN
            )


class Reactions(APIView):
    """List and toggle reactions"""

    def get(self, request):
        """List all reactions"""
        reactions = CommunicationService.list_reactions()
        serializer = TinyReactionSerializer(reactions, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Toggle reaction on comment"""
        comment_id = request.data.get("comment")
        user_id = request.data.get("user")
        
        if not comment_id:
            return Response(
                {"error": "Comment ID required"},
                status=HTTP_400_BAD_REQUEST
            )
        
        reaction, was_deleted = CommunicationService.toggle_comment_reaction(
            user_id=user_id,
            comment_id=comment_id
        )
        
        if was_deleted:
            return Response(status=HTTP_204_NO_CONTENT)
        
        serializer = TinyReactionSerializer(reaction)
        return Response(serializer.data, status=HTTP_201_CREATED)


class ReactionDetail(APIView):
    """Get, update, and delete reaction"""

    def get(self, request, pk):
        """Get reaction detail"""
        reaction = CommunicationService.get_reaction(pk)
        serializer = ReactionSerializer(reaction)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update reaction"""
        serializer = ReactionSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        reaction = CommunicationService.update_reaction(pk, request.user, serializer.validated_data)
        result = TinyReactionSerializer(reaction)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete reaction"""
        CommunicationService.delete_reaction(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
