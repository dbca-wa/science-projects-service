"""
User validation utilities
"""

from rest_framework.exceptions import ValidationError

from users.models import User


def validate_email_unique(email, exclude_user_id=None):
    """
    Validate that email is unique

    Args:
        email: Email to validate
        exclude_user_id: User ID to exclude from check (for updates)

    Raises:
        ValidationError: If email already exists
    """
    queryset = User.objects.filter(email=email)
    if exclude_user_id:
        queryset = queryset.exclude(id=exclude_user_id)

    if queryset.exists():
        raise ValidationError("Email already exists")


def validate_username_unique(username, exclude_user_id=None):
    """
    Validate that username is unique

    Args:
        username: Username to validate
        exclude_user_id: User ID to exclude from check (for updates)

    Raises:
        ValidationError: If username already exists
    """
    queryset = User.objects.filter(username=username)
    if exclude_user_id:
        queryset = queryset.exclude(id=exclude_user_id)

    if queryset.exists():
        raise ValidationError("Username already exists")


def validate_profile_data(data):
    """
    Validate profile data

    Args:
        data: Profile data dict

    Raises:
        ValidationError: If data is invalid
    """
    if "about" in data and len(data["about"]) > 5000:
        raise ValidationError("About section too long (max 5000 characters)")

    if "expertise" in data and len(data["expertise"]) > 2000:
        raise ValidationError("Expertise section too long (max 2000 characters)")


def validate_password_strength(password):
    """
    Validate password strength

    Args:
        password: Password to validate

    Raises:
        ValidationError: If password is too weak
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")

    if not any(char.isdigit() for char in password):
        raise ValidationError("Password must contain at least one digit")

    if not any(char.isupper() for char in password):
        raise ValidationError("Password must contain at least one uppercase letter")
