"""
User views
"""
from .auth import Login, Logout, ChangePassword
from .crud import Users, UserDetail, DirectorateUsers
from .utils import (
    CheckEmailExists,
    CheckNameExists,
    CheckUserIsStaff,
    Me,
    SmallInternalUserSearch,
)
from .admin import ToggleUserActive, SwitchAdmin
from .staff_profiles import (
    StaffProfiles,
    StaffProfileDetail,
    MyStaffProfile,
    TogglePublicVisibility,
    ActiveStaffProfileEmails,
    CheckStaffProfileAndReturnDataAndActiveState,
    DownloadBCSStaffCSV,
    StaffProfileProjects,
    PublicEmailStaffMember,
)
from .profile_sections import (
    StaffProfileHeroDetail,
    StaffProfileOverviewDetail,
    StaffProfileCVDetail,
)
from .profile_entries import (
    StaffProfileEmploymentEntries,
    StaffProfileEmploymentEntryDetail,
    StaffProfileEducationEntries,
    StaffProfileEducationEntryDetail,
    UserStaffEmploymentEntries,
    UserStaffEducationEntries,
)
from .user_profiles import (
    UserProfiles,
    UserProfileDetail,
    UpdatePersonalInformation,
    UpdateProfile,
    UpdateMembership,
    RemoveAvatar,
    UserWorks,
    UserWorkDetail,
    UsersProjects,
)

__all__ = [
    # Auth
    'Login',
    'Logout',
    'ChangePassword',
    # CRUD
    'Users',
    'UserDetail',
    'DirectorateUsers',
    # Utils
    'CheckEmailExists',
    'CheckNameExists',
    'CheckUserIsStaff',
    'Me',
    'SmallInternalUserSearch',
    # Admin
    'ToggleUserActive',
    'SwitchAdmin',
    # Staff Profiles
    'StaffProfiles',
    'StaffProfileDetail',
    'MyStaffProfile',
    'TogglePublicVisibility',
    'ActiveStaffProfileEmails',
    'CheckStaffProfileAndReturnDataAndActiveState',
    'DownloadBCSStaffCSV',
    'StaffProfileProjects',
    'PublicEmailStaffMember',
    # Profile Sections
    'StaffProfileHeroDetail',
    'StaffProfileOverviewDetail',
    'StaffProfileCVDetail',
    # Profile Entries
    'StaffProfileEmploymentEntries',
    'StaffProfileEmploymentEntryDetail',
    'StaffProfileEducationEntries',
    'StaffProfileEducationEntryDetail',
    'UserStaffEmploymentEntries',
    'UserStaffEducationEntries',
    # User Profiles
    'UserProfiles',
    'UserProfileDetail',
    'UpdatePersonalInformation',
    'UpdateProfile',
    'UpdateMembership',
    'RemoveAvatar',
    'UserWorks',
    'UserWorkDetail',
    'UsersProjects',
]
