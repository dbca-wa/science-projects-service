"""
User views
"""

from .admin import SwitchAdmin, ToggleUserActive
from .auth import ChangePassword, Login, Logout
from .crud import DirectorateUsers, UserDetail, Users
from .profile_entries import (
    StaffProfileEducationEntries,
    StaffProfileEducationEntryDetail,
    StaffProfileEmploymentEntries,
    StaffProfileEmploymentEntryDetail,
    UserStaffEducationEntries,
    UserStaffEmploymentEntries,
)
from .profile_sections import (
    StaffProfileCVDetail,
    StaffProfileHeroDetail,
    StaffProfileOverviewDetail,
)
from .staff_profiles import (
    ActiveStaffProfileEmails,
    CheckStaffProfileAndReturnDataAndActiveState,
    DownloadBCSStaffCSV,
    MyStaffProfile,
    PublicEmailStaffMember,
    StaffProfileDetail,
    StaffProfileProjects,
    StaffProfiles,
    TogglePublicVisibility,
)
from .user_profiles import (
    RemoveAvatar,
    UpdateMembership,
    UpdatePersonalInformation,
    UpdateProfile,
    UserProfileDetail,
    UserProfiles,
    UsersProjects,
    UserWorkDetail,
    UserWorks,
)
from .utils import (
    CheckEmailExists,
    CheckNameExists,
    CheckUserIsStaff,
    Me,
    SmallInternalUserSearch,
)

__all__ = [
    # Auth
    "Login",
    "Logout",
    "ChangePassword",
    # CRUD
    "Users",
    "UserDetail",
    "DirectorateUsers",
    # Utils
    "CheckEmailExists",
    "CheckNameExists",
    "CheckUserIsStaff",
    "Me",
    "SmallInternalUserSearch",
    # Admin
    "ToggleUserActive",
    "SwitchAdmin",
    # Staff Profiles
    "StaffProfiles",
    "StaffProfileDetail",
    "MyStaffProfile",
    "TogglePublicVisibility",
    "ActiveStaffProfileEmails",
    "CheckStaffProfileAndReturnDataAndActiveState",
    "DownloadBCSStaffCSV",
    "StaffProfileProjects",
    "PublicEmailStaffMember",
    # Profile Sections
    "StaffProfileHeroDetail",
    "StaffProfileOverviewDetail",
    "StaffProfileCVDetail",
    # Profile Entries
    "StaffProfileEmploymentEntries",
    "StaffProfileEmploymentEntryDetail",
    "StaffProfileEducationEntries",
    "StaffProfileEducationEntryDetail",
    "UserStaffEmploymentEntries",
    "UserStaffEducationEntries",
    # User Profiles
    "UserProfiles",
    "UserProfileDetail",
    "UpdatePersonalInformation",
    "UpdateProfile",
    "UpdateMembership",
    "RemoveAvatar",
    "UserWorks",
    "UserWorkDetail",
    "UsersProjects",
]
