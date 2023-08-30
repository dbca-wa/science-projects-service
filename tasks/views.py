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
from .models import Task
from .serializers import TaskSerializer, TinyTaskSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class Tasks(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, req):
        tasks = Tasks.objects.all()
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
        # print(req.data)
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
            return Response(
                HTTP_400_BAD_REQUEST,
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
        task.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        # print(req.data)
        task = self.go(pk)
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
        tasks = Task.objects.filter(user=req.user).order_by("-created_at")

        # print(tasks)

        # Split the tasks into separate arrays based on their status
        tasks_by_status = {
            "done": [],
            "todo": [],
            "inprogress": [],
        }

        for task in tasks:
            status = (
                task.status
                # task.get_status_display()
            )  # Get the human-readable status from choices
            # print(status)
            if status in tasks_by_status:
                tasks_by_status[status].append(task)

        # Serialize the tasks in each array using TinyTaskSerializer
        tasks_data = {
            "done": TinyTaskSerializer(
                tasks_by_status["done"], many=True, context={"request": req}
            ).data,
            "todo": TinyTaskSerializer(
                tasks_by_status["todo"], many=True, context={"request": req}
            ).data,
            "inprogress": TinyTaskSerializer(
                tasks_by_status["inprogress"], many=True, context={"request": req}
            ).data,
        }

        return Response(
            tasks_data,
            status=HTTP_200_OK,
        )
