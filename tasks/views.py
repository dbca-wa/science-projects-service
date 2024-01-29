import os
import random
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.exceptions import (
    NotFound,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from django.db import transaction
from .models import Task, UserFeedback
from .serializers import (
    TaskSerializer,
    TinyTaskSerializer,
    UserFeedbackCreationSerializer,
    UserFeedbackSerializer,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class Tasks(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        tasks = Task.objects.all()
        ser = TinyTaskSerializer(
            tasks,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating task")
        ser = TaskSerializer(
            data=req.data,
        )
        if ser.is_valid():
            task = ser.save()
            return Response(
                TinyTaskSerializer(task).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                HTTP_400_BAD_REQUEST,
            )


class Feedbacks(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        feedbacks = UserFeedback.objects.all()
        ser = UserFeedbackSerializer(
            feedbacks,
            many=True,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is posting feedback")

        ser = UserFeedbackCreationSerializer(
            data=req.data,
        )
        if ser.is_valid():
            feedback = ser.save()
            return Response(
                UserFeedbackSerializer(feedback).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                HTTP_400_BAD_REQUEST,
            )


class FeedbackDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = UserFeedback.objects.get(pk=pk)
        except UserFeedback.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        feedback = self.go(pk)
        ser = UserFeedbackSerializer(
            feedback,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        feedback = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting feedback: {feedback}")
        feedback.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        feedback = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating feedback: {feedback}")
        ser = UserFeedbackSerializer(
            feedback,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_feedback = ser.save()
            return Response(
                UserFeedbackSerializer(updated_feedback).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class TaskDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def go(self, pk):
        try:
            obj = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        task = self.go(pk)
        ser = TaskSerializer(
            task,
            context={"request": req},
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting task: {task}")
        task.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        task = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating task: {task}")
        ser = TaskSerializer(
            task,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_task = ser.save()
            return Response(
                TinyTaskSerializer(updated_task).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class MyTasks(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        # Handle not logged in
        if not req.user.is_authenticated:
            return Response(
                {"detail": "You are not logged in."}, status=HTTP_401_UNAUTHORIZED
            )

        # Fetch tasks that belong to the authenticated user (req.user) and order by date added
        tasks = Task.objects.select_related('user').filter(user=req.user).order_by("-created_at")

        return Response(
            TinyTaskSerializer(tasks, many=True).data,
            status=HTTP_200_OK,
        )