"""
Project views
"""
from .crud import Projects, ProjectDetails
from .map import ProjectMap
from .search import SmallProjectSearch, MyProjects
from .details import (
    ProjectAdditional,
    ProjectAdditionalDetail,
    StudentProjectAdditional,
    StudentProjectAdditionalDetail,
    ExternalProjectAdditional,
    ExternalProjectAdditionalDetail,
    SelectedProjectAdditionalDetail,
)
from .members import (
    ProjectMembers,
    ProjectMemberDetail,
    ProjectLeaderDetail,
    MembersForProject,
    PromoteToLeader,
)
from .areas import ProjectAreas, ProjectAreaDetail, AreasForProject
from .admin import (
    UnapprovedThisFY,
    ProblematicProjects,
    RemedyOpenClosed,
    RemedyMemberlessProjects,
    RemedyNoLeaderProjects,
    RemedyMultipleLeaderProjects,
    RemedyExternalLeaderProjects,
)
from .export import DownloadAllProjectsAsCSV, DownloadARProjectsAsCSV
from .utils import (
    ProjectYears,
    SuspendProject,
    ProjectDocs,
    ToggleUserProfileVisibilityForProject,
    CoreFunctionProjects,
    ScienceProjects,
    StudentProjects,
    ExternalProjects,
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
