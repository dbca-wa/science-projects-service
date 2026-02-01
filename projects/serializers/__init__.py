"""
Project serializers

Temporary compatibility layer - exports from serializers_old.py
until projects app refactoring is complete.
"""
from .serializers_old import (
    # Used by other apps
    ProjectDataTableSerializer,
    MiniProjectMemberSerializer,
    ProjectAreaSerializer,
    TinyProjectSerializer,
    TinyStudentProjectARSerializer,
    ProblematicProjectSerializer,
    ARExternalProjectSerializer,
    ProjectSerializer,
    # Used by projects views
    CreateProjectSerializer,
    ExternalProjectDetailSerializer,
    ProjectDetailSerializer,
    ProjectDetailViewSerializer,
    ProjectMemberSerializer,
    ProjectUpdateSerializer,
    StudentProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
    TinyProjectDetailSerializer,
    TinyProjectMemberSerializer,
    TinyStudentProjectDetailSerializer,
)

__all__ = [
    'ProjectDataTableSerializer',
    'MiniProjectMemberSerializer',
    'ProjectAreaSerializer',
    'TinyProjectSerializer',
    'TinyStudentProjectARSerializer',
    'ProblematicProjectSerializer',
    'ARExternalProjectSerializer',
    'ProjectSerializer',
    'CreateProjectSerializer',
    'ExternalProjectDetailSerializer',
    'ProjectDetailSerializer',
    'ProjectDetailViewSerializer',
    'ProjectMemberSerializer',
    'ProjectUpdateSerializer',
    'StudentProjectDetailSerializer',
    'TinyExternalProjectDetailSerializer',
    'TinyProjectDetailSerializer',
    'TinyProjectMemberSerializer',
    'TinyStudentProjectDetailSerializer',
]

