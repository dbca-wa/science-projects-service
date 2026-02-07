"""
User serializers
"""

from .base import (
    BasicUserSerializer,
    MiniUserSerializer,
    PrivateTinyUserSerializer,
    StaffProfileEmailListSerializer,
    TinyUserSerializer,
    TinyUserWorkSerializer,
    UserMeSerializer,
    UserSerializer,
    UserWorkSerializer,
)
from .entries import (
    EducationEntryCreationSerializer,
    EducationEntrySerializer,
    EmploymentEntryCreationSerializer,
    EmploymentEntrySerializer,
)
from .profile import (
    ProfilePageSerializer,
    TinyUserProfileSerializer,
    UserProfileSerializer,
)
from .staff_profile import (
    KeywordTagSerializer,
    StaffProfileCreationSerializer,
    StaffProfileCVSerializer,
    StaffProfileHeroSerializer,
    StaffProfileOverviewSerializer,
    StaffProfileSerializer,
    TinyStaffProfileSerializer,
)
from .update import (
    UpdateMembershipSerializer,
    UpdatePISerializer,
    UpdateProfileSerializer,
    UserWorkAffiliationUpdateSerializer,
)

__all__ = [
    # Base
    "UserSerializer",
    "TinyUserSerializer",
    "PrivateTinyUserSerializer",
    "MiniUserSerializer",
    "BasicUserSerializer",
    "StaffProfileEmailListSerializer",
    "TinyUserWorkSerializer",
    "UserWorkSerializer",
    "UserMeSerializer",
    # Profile
    "TinyUserProfileSerializer",
    "UserProfileSerializer",
    "ProfilePageSerializer",
    # Staff Profile
    "KeywordTagSerializer",
    "TinyStaffProfileSerializer",
    "StaffProfileCreationSerializer",
    "StaffProfileHeroSerializer",
    "StaffProfileOverviewSerializer",
    "StaffProfileCVSerializer",
    "StaffProfileSerializer",
    # Entries
    "EmploymentEntrySerializer",
    "EmploymentEntryCreationSerializer",
    "EducationEntrySerializer",
    "EducationEntryCreationSerializer",
    # Update
    "UpdatePISerializer",
    "UpdateProfileSerializer",
    "UpdateMembershipSerializer",
    "UserWorkAffiliationUpdateSerializer",
]
