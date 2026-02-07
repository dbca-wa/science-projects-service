"""
Project serializers
"""

# Project area serializers
from .areas import ProjectAreaSerializer

# Base project serializers
from .base import (
    CreateProjectSerializer,
    PkAndKindOnlyProjectSerializer,
    ProblematicProjectSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    TinyProjectSerializer,
    UserProfileProjectSerializer,
)

# Project details serializers
from .details import (
    ExternalProjectDetailSerializer,
    ProjectDetailSerializer,
    ProjectDetailViewSerializer,
    StudentProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
    TinyProjectDetailSerializer,
    TinyStudentProjectDetailSerializer,
)

# Export serializers
from .export import (
    ARExternalProjectSerializer,
    ARProjectSerializer,
    ProjectDataTableSerializer,
    TinyStudentProjectARSerializer,
)

# Project member serializers
from .members import (
    MiniProjectMemberSerializer,
    MiniUserSerializer,
    ProjectMemberSerializer,
    TinyProjectMemberSerializer,
)

__all__ = [
    # Base
    "CreateProjectSerializer",
    "ProjectSerializer",
    "ProjectUpdateSerializer",
    "TinyProjectSerializer",
    "ProblematicProjectSerializer",
    "UserProfileProjectSerializer",
    "PkAndKindOnlyProjectSerializer",
    # Details
    "ProjectDetailSerializer",
    "ProjectDetailViewSerializer",
    "TinyProjectDetailSerializer",
    "StudentProjectDetailSerializer",
    "TinyStudentProjectDetailSerializer",
    "ExternalProjectDetailSerializer",
    "TinyExternalProjectDetailSerializer",
    # Members
    "ProjectMemberSerializer",
    "TinyProjectMemberSerializer",
    "MiniProjectMemberSerializer",
    "MiniUserSerializer",
    # Areas
    "ProjectAreaSerializer",
    # Export
    "ARProjectSerializer",
    "ARExternalProjectSerializer",
    "TinyStudentProjectARSerializer",
    "ProjectDataTableSerializer",
]
