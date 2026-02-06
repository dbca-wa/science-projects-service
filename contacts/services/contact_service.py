"""
Contact service - Business logic for contact operations
"""
from django.conf import settings
from rest_framework.exceptions import NotFound

from contacts.models import UserContact, BranchContact, AgencyContact, Address


class ContactService:
    """Business logic for contact operations"""

    # Address operations
    @staticmethod
    def list_addresses():
        """List all addresses"""
        return Address.objects.all()

    @staticmethod
    def get_address(pk):
        """Get address by ID"""
        try:
            return Address.objects.get(pk=pk)
        except Address.DoesNotExist:
            raise NotFound(f"Address {pk} not found")

    @staticmethod
    def create_address(user, data):
        """Create new address"""
        settings.LOGGER.info(f"{user} is creating address")
        return Address.objects.create(**data)

    @staticmethod
    def update_address(pk, user, data):
        """Update address"""
        address = ContactService.get_address(pk)
        settings.LOGGER.info(f"{user} is updating address {address}")
        
        for field, value in data.items():
            setattr(address, field, value)
        address.save()
        
        return address

    @staticmethod
    def delete_address(pk, user):
        """Delete address"""
        address = ContactService.get_address(pk)
        settings.LOGGER.info(f"{user} is deleting address {address}")
        address.delete()

    # Agency contact operations
    @staticmethod
    def list_agency_contacts():
        """List all agency contacts"""
        return AgencyContact.objects.all()

    @staticmethod
    def get_agency_contact(pk):
        """Get agency contact by ID"""
        try:
            return AgencyContact.objects.get(pk=pk)
        except AgencyContact.DoesNotExist:
            raise NotFound(f"Agency contact {pk} not found")

    @staticmethod
    def create_agency_contact(user, data):
        """Create new agency contact"""
        settings.LOGGER.info(f"{user} is creating agency contact")
        return AgencyContact.objects.create(**data)

    @staticmethod
    def update_agency_contact(pk, user, data):
        """Update agency contact"""
        contact = ContactService.get_agency_contact(pk)
        settings.LOGGER.info(f"{user} is updating agency contact {contact}")
        
        for field, value in data.items():
            setattr(contact, field, value)
        contact.save()
        
        return contact

    @staticmethod
    def delete_agency_contact(pk, user):
        """Delete agency contact"""
        contact = ContactService.get_agency_contact(pk)
        settings.LOGGER.info(f"{user} is deleting agency contact {contact}")
        contact.delete()

    # Branch contact operations
    @staticmethod
    def list_branch_contacts():
        """List all branch contacts"""
        return BranchContact.objects.all()

    @staticmethod
    def get_branch_contact(pk):
        """Get branch contact by ID"""
        try:
            return BranchContact.objects.get(pk=pk)
        except BranchContact.DoesNotExist:
            raise NotFound(f"Branch contact {pk} not found")

    @staticmethod
    def create_branch_contact(user, data):
        """Create new branch contact"""
        settings.LOGGER.info(f"{user} is creating branch contact")
        return BranchContact.objects.create(**data)

    @staticmethod
    def update_branch_contact(pk, user, data):
        """Update branch contact"""
        contact = ContactService.get_branch_contact(pk)
        settings.LOGGER.info(f"{user} is updating branch contact {contact}")
        
        for field, value in data.items():
            setattr(contact, field, value)
        contact.save()
        
        return contact

    @staticmethod
    def delete_branch_contact(pk, user):
        """Delete branch contact"""
        contact = ContactService.get_branch_contact(pk)
        settings.LOGGER.info(f"{user} is deleting branch contact {contact}")
        contact.delete()

    # User contact operations
    @staticmethod
    def list_user_contacts():
        """List all user contacts"""
        return UserContact.objects.all()

    @staticmethod
    def get_user_contact(pk):
        """Get user contact by ID"""
        try:
            return UserContact.objects.get(pk=pk)
        except UserContact.DoesNotExist:
            raise NotFound(f"User contact {pk} not found")

    @staticmethod
    def create_user_contact(user, data):
        """Create new user contact"""
        settings.LOGGER.info(f"{user} is creating user contact")
        return UserContact.objects.create(**data)

    @staticmethod
    def update_user_contact(pk, user, data):
        """Update user contact"""
        contact = ContactService.get_user_contact(pk)
        settings.LOGGER.info(f"{user} is updating user contact {contact}")
        
        for field, value in data.items():
            setattr(contact, field, value)
        contact.save()
        
        return contact

    @staticmethod
    def delete_user_contact(pk, user):
        """Delete user contact"""
        contact = ContactService.get_user_contact(pk)
        settings.LOGGER.info(f"{user} is deleting user contact {contact}")
        contact.delete()
