# Custom exceptions for validation pipeline
"""
Custom exception classes for data validation and cleaning pipelines.
"""

from scrapy.exceptions import DropItem


class ValidationError(DropItem):
    """Base exception for validation errors."""
    def __init__(self, message: str, field: str = None, item_url: str = None):
        self.field = field
        self.item_url = item_url
        super().__init__(f"Validation Error: {message}")


class RequiredFieldMissingError(ValidationError):
    """Raised when a required field is missing."""
    def __init__(self, field: str, item_url: str = None):
        super().__init__(
            f"Required field '{field}' is missing or empty", 
            field=field, 
            item_url=item_url
        )


class DataTypeError(ValidationError):
    """Raised when a field has an incorrect data type."""
    def __init__(self, field: str, expected_type: str, actual_type: str, item_url: str = None):
        super().__init__(
            f"Field '{field}' expected type '{expected_type}' but got '{actual_type}'",
            field=field,
            item_url=item_url
        )


class DateFormatError(ValidationError):
    """Raised when a date field has an invalid format."""
    def __init__(self, field: str, value: str, expected_format: str, item_url: str = None):
        super().__init__(
            f"Field '{field}' with value '{value}' does not match expected format '{expected_format}'",
            field=field,
            item_url=item_url
        )


class CleaningError(Exception):
    """Base exception for cleaning errors."""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(f"Cleaning Error: {message}")
