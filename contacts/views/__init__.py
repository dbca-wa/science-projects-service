"""
Contact views
"""
from .addresses import Addresses, AddressDetail
from .contacts import (
    AgencyContacts,
    AgencyContactDetail,
    BranchContacts,
    BranchContactDetail,
    UserContacts,
    UserContactDetail,
)

__all__ = [
    'Addresses',
    'AddressDetail',
    'AgencyContacts',
    'AgencyContactDetail',
    'BranchContacts',
    'BranchContactDetail',
    'UserContacts',
    'UserContactDetail',
]
