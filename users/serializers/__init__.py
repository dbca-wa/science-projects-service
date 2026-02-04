"""
User serializers
"""
from .base import (
    UserSerializer,
    TinyUserSerializer,
    PrivateTinyUserSerializer,
    MiniUserSerializer,
    BasicUserSerializer,
    StaffProfileEmailListSerializer,
    TinyUserWorkSerializer,
    UserWorkSerializer,
    UserMeSerializer,
)
from .profile import (
    TinyUserProfileSerializer,
    UserProfileSerializer,
    ProfilePageSerializer,
)
from .staff_profile import (
    KeywordTagSerializer,
    TinyStaffProfileSerializer,
    StaffProfileCreationSerializer,
    StaffProfileHeroSerializer,
    StaffProfileOverviewSerializer,
    StaffProfileCVSerializer,
    StaffProfileSerializer,
)
from .entries import (
    EmploymentEntrySerializer,
    EmploymentEntryCreationSerializer,
    EducationEntrySerializer,
    EducationEntryCreationSerializer,
)
from .update import (
    UpdatePISerializer,
    UpdateProfileSerializer,
    UpdateMembershipSerializer,
    UserWorkAffiliationUpdateSerializer,
)

__all__ = [
    # Base
    'UserSerializer',
    'TinyUserSerializer',
    'PrivateTinyUserSerializer',
    'MiniUserSerializer',
    'BasicUserSerializer',
    'StaffProfileEmailListSerializer',
    'TinyUserWorkSerializer',
    'UserWorkSerializer',
    'UserMeSerializer',
    # Profile
    'TinyUserProfileSerializer',
    'UserProfileSerializer',
    'ProfilePageSerializer',
    # Staff Profile
    'KeywordTagSerializer',
    'TinyStaffProfileSerializer',
    'StaffProfileCreationSerializer',
    'StaffProfileHeroSerializer',
    'StaffProfileOverviewSerializer',
    'StaffProfileCVSerializer',
    'StaffProfileSerializer',
    # Entries
    'EmploymentEntrySerializer',
    'EmploymentEntryCreationSerializer',
    'EducationEntrySerializer',
    'EducationEntryCreationSerializer',
    # Update
    'UpdatePISerializer',
    'UpdateProfileSerializer',
    'UpdateMembershipSerializer',
    'UserWorkAffiliationUpdateSerializer',
]
