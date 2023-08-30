from rest_framework.serializers import (
    ModelSerializer,
    DateTimeField,
    SerializerMethodField,
)

from medias.serializers import BusinessAreaPhotoSerializer
from .models import Task


class TinyTaskSerializer(ModelSerializer):
    creator = SerializerMethodField()
    user = SerializerMethodField()
    project = SerializerMethodField()
    date_assigned = DateTimeField(source="created_at")

    class Meta:
        model = Task
        fields = [
            "pk",
            "creator",
            "user",
            "project",
            "document",
            "name",
            "description",
            "notes",
            "status",
            "task_type",
            "date_assigned",
        ]

    def get_creator(self, obj):
        creator_data = {
            "pk": obj.creator.pk,
            "first_name": obj.creator.first_name,
            "last_name": obj.creator.last_name,
        }
        return creator_data

    def get_user(self, obj):
        user_data = {
            "pk": obj.user.pk,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
        }
        return user_data

    def get_project(self, obj):
        if obj.project:
            project_data = {
                "pk": obj.project.pk,
                "title": obj.project.title,
                "status": obj.project.status,
                "kind": obj.project.kind,
                "year": obj.project.year,
                "business_area": {
                    "pk": obj.project.business_area.pk,
                    "name": obj.project.business_area.name,
                    "slug": obj.project.business_area.slug,
                    "leader_id": obj.project.business_area.leader_id,
                    "focus": obj.project.business_area.focus,
                    "introduction": obj.project.business_area.introduction,
                    "image": BusinessAreaPhotoSerializer(
                        obj.project.business_area.image
                    ).data,
                },
            }
            # Check if the image exists, and if so, include the image data
            if hasattr(obj.project, "image"):
                project_data["image"] = {
                    "pk": obj.project.image.pk if obj.project.image else None,
                    "file": obj.project.image.file.url
                    if obj.project.image and obj.project.image.file
                    else None,
                    "old_file": obj.project.image.old_file
                    if obj.project.image
                    else None,
                }
            else:
                project_data["image"] = None

            return project_data

        else:
            return None


class TaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
