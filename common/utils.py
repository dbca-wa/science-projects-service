class TeamMemberMixin:
    def get_team_members(self, obj):
        from projects.models import ProjectMember
        from projects.serializers import MiniProjectMemberSerializer

        project = obj.document.project
        if (
            hasattr(project, "_prefetched_objects_cache")
            and "members" in project._prefetched_objects_cache
        ):
            members = project._prefetched_objects_cache["members"]
        else:
            members = (
                ProjectMember.objects.select_related(
                    "user", "user__profile", "user__work", "user__work__business_area"
                )
                .prefetch_related("user__caretaker", "user__caretaker_for")
                .filter(project=project.pk)
                .all()
            )
        return MiniProjectMemberSerializer(members, many=True).data


class ProjectTeamMemberMixin:
    def get_team_members(self, project):
        from projects.models import ProjectMember
        from projects.serializers import MiniProjectMemberSerializer

        if (
            hasattr(project, "_prefetched_objects_cache")
            and "members" in project._prefetched_objects_cache
        ):
            members = project._prefetched_objects_cache["members"]
        else:
            members = (
                ProjectMember.objects.select_related(
                    "user", "user__profile", "user__work", "user__work__business_area"
                )
                .prefetch_related("user__caretaker", "user__caretaker_for")
                .filter(project=project.pk)
                .all()
            )
        return MiniProjectMemberSerializer(members, many=True).data
