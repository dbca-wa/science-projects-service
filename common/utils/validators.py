"""
Common validation utilities
"""

from rest_framework import serializers


def validate_not_empty(value, field_name="Field"):
    """
    Validate that a string value is not empty or whitespace

    Args:
        value: String value to validate
        field_name: Name of field for error message

    Returns:
        Validated value

    Raises:
        ValidationError: If value is empty or whitespace

    Example:
        def validate_title(self, value):
            return validate_not_empty(value, "Title")
    """
    if not value or not value.strip():
        raise serializers.ValidationError(f"{field_name} cannot be empty")
    return value.strip()


def validate_date_range(
    start_date, end_date, start_field="start_date", end_field="end_date"
):
    """
    Validate that start date is before end date

    Args:
        start_date: Start date
        end_date: End date
        start_field: Name of start date field for error message
        end_field: Name of end date field for error message

    Raises:
        ValidationError: If start date is after end date

    Example:
        def validate(self, data):
            if 'start_date' in data and 'end_date' in data:
                validate_date_range(data['start_date'], data['end_date'])
            return data
    """
    if start_date and end_date and start_date > end_date:
        raise serializers.ValidationError(
            {
                end_field: f"{end_field.replace('_', ' ').title()} must be after {start_field.replace('_', ' ')}"
            }
        )


def validate_positive_number(value, field_name="Value"):
    """
    Validate that a number is positive

    Args:
        value: Number to validate
        field_name: Name of field for error message

    Returns:
        Validated value

    Raises:
        ValidationError: If value is not positive

    Example:
        def validate_amount(self, value):
            return validate_positive_number(value, "Amount")
    """
    if value is not None and value <= 0:
        raise serializers.ValidationError(f"{field_name} must be positive")
    return value


def validate_file_size(file, max_size_mb=10):
    """
    Validate file size

    Args:
        file: Uploaded file object
        max_size_mb: Maximum file size in megabytes

    Raises:
        ValidationError: If file exceeds max size

    Example:
        def validate_document(self, value):
            validate_file_size(value, max_size_mb=5)
            return value
    """
    if file and file.size > max_size_mb * 1024 * 1024:
        raise serializers.ValidationError(f"File size cannot exceed {max_size_mb}MB")


def validate_file_extension(file, allowed_extensions):
    """
    Validate file extension

    Args:
        file: Uploaded file object
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.doc'])

    Raises:
        ValidationError: If file extension not allowed

    Example:
        def validate_document(self, value):
            validate_file_extension(value, ['.pdf', '.docx'])
            return value
    """
    if file:
        import os

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
