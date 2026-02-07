"""
Project views
"""

from .admin import (
    ProblematicProjects,
    RemedyExternalLeaderProjects,
    RemedyMemberlessProjects,
    RemedyMultipleLeaderProjects,
    RemedyNoLeaderProjects,
    RemedyOpenClosed,
    UnapprovedThisFY,
)
from .areas import AreasForProject, ProjectAreaDetail, ProjectAreas
from .crud import ProjectDetails, Projects
from .details import (
    ExternalProjectAdditional,
    ExternalProjectAdditionalDetail,
    ProjectAdditional,
    ProjectAdditionalDetail,
    SelectedProjectAdditionalDetail,
    StudentProjectAdditional,
    StudentProjectAdditionalDetail,
)
from .export import DownloadAllProjectsAsCSV, DownloadARProjectsAsCSV
from .map import ProjectMap
from .members import (
    MembersForProject,
    ProjectLeaderDetail,
    ProjectMemberDetail,
    ProjectMembers,
    PromoteToLeader,
)
from .search import MyProjects, SmallProjectSearch
from .utils import (
    CoreFunctionProjects,
    ExternalProjects,
    ProjectDocs,
    ProjectYears,
    ScienceProjects,
    StudentProjects,
    SuspendProject,
    ToggleUserProfileVisibilityForProject,
)

__all__ = [
    # CRUD
    "Projects",
    "ProjectDetails",
    # Map
    "ProjectMap",
    # Search
    "SmallProjectSearch",
    "MyProjects",
    # Details
    "ProjectAdditional",
    "ProjectAdditionalDetail",
    "StudentProjectAdditional",
    "StudentProjectAdditionalDetail",
    "ExternalProjectAdditional",
    "ExternalProjectAdditionalDetail",
    "SelectedProjectAdditionalDetail",
    # Members
    "ProjectMembers",
    "ProjectMemberDetail",
    "ProjectLeaderDetail",
    "MembersForProject",
    "PromoteToLeader",
    # Areas
    "ProjectAreas",
    "ProjectAreaDetail",
    "AreasForProject",
    # Admin
    "UnapprovedThisFY",
    "ProblematicProjects",
    "RemedyOpenClosed",
    "RemedyMemberlessProjects",
    "RemedyNoLeaderProjects",
    "RemedyMultipleLeaderProjects",
    "RemedyExternalLeaderProjects",
    # Export
    "DownloadAllProjectsAsCSV",
    "DownloadARProjectsAsCSV",
    # Utils
    "ProjectYears",
    "SuspendProject",
    "ProjectDocs",
    "ToggleUserProfileVisibilityForProject",
    "CoreFunctionProjects",
    "ScienceProjects",
    "StudentProjects",
    "ExternalProjects",
]
