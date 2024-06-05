from rest_framework.exceptions import (
    NotFound,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.db import transaction
from django.conf import settings
from django.utils import timezone

import time

from .models import Comment, DirectMessage, ChatRoom, Reaction
from .serializers import (
    ChatRoomSerializer,
    CommentSerializer,
    DirectMessageSerializer,
    ReactionCreateSerializer,
    ReactionSerializer,
    TinyChatRoomSerializer,
    TinyCommentSerializer,
    TinyDirectMessageSerializer,
    TinyReactionSerializer,
)


class ChatRooms(APIView):
    def get(self, req):
        all = ChatRoom.objects.all()
        ser = TinyChatRoomSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating a chat room")
        ser = ChatRoomSerializer(data=req.data)
        if ser.is_valid():
            cr = ser.save()
            return Response(
                TinyChatRoomSerializer(cr).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DirectMessages(APIView):
    def get(self, req):
        all = DirectMessage.objects.all()
        ser = TinyDirectMessageSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a dm")
        ser = DirectMessageSerializer(data=req.data)
        if ser.is_valid():
            dm = ser.save()
            return Response(
                TinyDirectMessageSerializer(dm).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class Comments(APIView):
    def get(self, req):
        all = Comment.objects.all()
        ser = TinyCommentSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting a comment")
        ser = CommentSerializer(data=req.data)
        if ser.is_valid():
            comment = ser.save()
            return Response(
                TinyCommentSerializer(comment).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class Reactions(APIView):
    def get(self, req):
        all = Reaction.objects.all()
        ser = TinyReactionSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        if req.data.get("comment"):
            settings.LOGGER.info(msg=f"{req.user} is reacting to a comment")
            data = {
                # "comment": get_comment(),
                "comment": int(req.data.get("comment")),
                "user": req.data.get("user")["pk"],
                "reaction": Reaction.ReactionChoices.THUMBUP,
                "direct_message": None,
            }

            # First check if there is a reaction by that user for the comment
            exists = Reaction.objects.filter(
                user=int(req.data.get("user")["pk"]),
                reaction=Reaction.ReactionChoices.THUMBUP,
                comment=int(req.data.get("comment")),
            ).first()
            if exists:
                exists.delete()
                return Response(
                    status=HTTP_204_NO_CONTENT,
                )

            #  if req.data.get("reaction") == "thumbup" else Reaction.ReactionChoices.THUMBUP
            ser = ReactionCreateSerializer(data=data)
            if ser.is_valid():
                dm_reaction = ser.save()
                return Response(
                    TinyReactionSerializer(dm_reaction).data,
                    status=HTTP_201_CREATED,
                )
            else:
                settings.LOGGER.error(msg=f"{ser.errors}")
                return Response(
                    ser.errors,
                    status=HTTP_400_BAD_REQUEST,
                )
        else:
            settings.LOGGER.info(
                msg=f"{req.user} tried to react to something but no comment data was found"
            )
            return Response(
                status=HTTP_400_BAD_REQUEST,
            )


# Details
class ChatRoomDetail(APIView):
    def go(self, pk):
        try:
            obj = ChatRoom.objects.get(pk=pk)
        except ChatRoom.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        cr = self.go(pk)
        ser = ChatRoomSerializer(cr)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        cr = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting a chat room {cr}")
        cr.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        cr = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating a chat room {cr}")
        ser = ChatRoomSerializer(
            cr,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            return Response(
                TinyChatRoomSerializer(updated).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class DirectMessageDetail(APIView):
    def go(self, pk):
        try:
            obj = DirectMessage.objects.get(pk=pk)
        except DirectMessage.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        dm = self.go(pk)
        ser = DirectMessageSerializer(dm)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        dm = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting a dm {dm}")
        dm.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        dm = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating a dm {dm}")
        ser = DirectMessageSerializer(
            dm,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            return Response(
                TinyDirectMessageSerializer(updated).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.info(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class CommentDetail(APIView):
    def go(self, pk):
        try:
            obj = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        comment = self.go(pk)
        ser = CommentSerializer(comment)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        comment = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting a comment detail {comment}")
        comment.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        comment = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating a comment detail {comment}")
        ser = CommentSerializer(
            comment,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            return Response(
                TinyCommentSerializer(updated).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class ReactionDetail(APIView):
    def go(self, pk):
        try:
            obj = Reaction.objects.get(pk=pk)
        except Reaction.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        reaction = self.go(pk)
        ser = ReactionSerializer(reaction)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        dmr = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting a reaction detail {dmr}")
        dmr.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        reaction = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating a reaction detail {reaction}")
        ser = ReactionSerializer(
            reaction,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated = ser.save()
            return Response(
                TinyReactionSerializer(updated).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )
