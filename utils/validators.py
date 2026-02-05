"""Input validation framework for security"""

import re
from typing import Any, List, Optional
from html import escape


class ValidationError(Exception):
    """Raised when validation fails"""

    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.message = message
        self.field = field


class InputValidator:
    """Comprehensive input validation for security"""

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('.*--)",
        r"(UNION.*SELECT)",
        r"(xp_cmdshell)",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    @staticmethod
    def validate_sql_safe(value: str, field_name: str = "input") -> str:
        """
        Validate input is safe from SQL injection

        Args:
            value: Input string to validate
            field_name: Name of the field for error messages

        Returns:
            Validated string

        Raises:
            ValidationError: If SQL injection pattern detected
        """
        if not isinstance(value, str):
            return value

        # Check for SQL injection patterns
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    f"Potentially dangerous SQL pattern detected in {field_name}",
                    field_name,
                )

        return value

    @staticmethod
    def validate_xss_safe(value: str, field_name: str = "input") -> str:
        """
        Validate input is safe from XSS attacks

        Args:
            value: Input string to validate
            field_name: Name of the field for error messages

        Returns:
            Sanitized string with HTML escaped

        Raises:
            ValidationError: If XSS pattern detected
        """
        if not isinstance(value, str):
            return value

        # Check for XSS patterns
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    f"Potentially dangerous XSS pattern detected in {field_name}",
                    field_name,
                )

        # Escape HTML entities
        return escape(value)

    @staticmethod
    def validate_numeric(
        value: Any,
        field_name: str = "input",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> float:
        """
        Validate numeric input

        Args:
            value: Input value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Validated numeric value

        Raises:
            ValidationError: If validation fails
        """
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number", field_name)

        if min_value is not None and num_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}", field_name
            )

        if max_value is not None and num_value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}", field_name
            )

        return num_value

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str = "input",
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> int:
        """
        Validate integer input

        Args:
            value: Input value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Validated integer value

        Raises:
            ValidationError: If validation fails
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer", field_name)

        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}", field_name
            )

        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}", field_name
            )

        return int_value

    @staticmethod
    def validate_string(
        value: Any,
        field_name: str = "input",
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Validate string input

        Args:
            value: Input value to validate
            field_name: Name of the field for error messages
            min_length: Minimum string length
            max_length: Maximum string length
            pattern: Regex pattern to match

        Returns:
            Validated string

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field_name)

        if min_length is not None and len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters", field_name
            )

        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters", field_name
            )

        if pattern is not None and not re.match(pattern, value):
            raise ValidationError(
                f"{field_name} does not match required pattern", field_name
            )

        return value

    @staticmethod
    def validate_email(value: str, field_name: str = "email") -> str:
        """
        Validate email address

        Args:
            value: Email address to validate
            field_name: Name of the field for error messages

        Returns:
            Validated email address

        Raises:
            ValidationError: If email is invalid
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, value):
            raise ValidationError(
                f"{field_name} is not a valid email address", field_name
            )

        return value

    @staticmethod
    def validate_url(
        value: str, field_name: str = "url", allowed_schemes: List[str] = None
    ) -> str:
        """
        Validate URL

        Args:
            value: URL to validate
            field_name: Name of the field for error messages
            allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if allowed_schemes is None:
            allowed_schemes = ["http", "https"]

        url_pattern = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"

        if not re.match(url_pattern, value, re.IGNORECASE):
            raise ValidationError(f"{field_name} is not a valid URL", field_name)

        # Check scheme
        scheme = value.split("://")[0].lower()
        if scheme not in allowed_schemes:
            raise ValidationError(
                f"{field_name} must use one of these schemes: {', '.join(allowed_schemes)}",
                field_name,
            )

        return value

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove path separators and special characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Prevent directory traversal
        sanitized = sanitized.replace("..", "")

        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]

        return sanitized

    @staticmethod
    def validate_json_structure(
        data: dict, required_fields: List[str], field_name: str = "data"
    ) -> dict:
        """
        Validate JSON structure has required fields

        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            field_name: Name of the field for error messages

        Returns:
            Validated dictionary

        Raises:
            ValidationError: If required fields are missing
        """
        if not isinstance(data, dict):
            raise ValidationError(f"{field_name} must be a dictionary", field_name)

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValidationError(
                f"{field_name} is missing required fields: {', '.join(missing_fields)}",
                field_name,
            )

        return data


class SQLSafeQuery:
    """Helper class for building SQL-safe parameterized queries"""

    @staticmethod
    def build_select(
        table: str,
        columns: List[str] = None,
        where_clause: str = None,
        params: tuple = None,
    ) -> tuple:
        """
        Build a safe SELECT query with parameterized values

        Args:
            table: Table name (validated)
            columns: List of column names (validated)
            where_clause: WHERE clause with ? placeholders
            params: Tuple of parameter values

        Returns:
            Tuple of (query_string, params)
        """
        # Validate table name (alphanumeric and underscore only)
        if not re.match(r"^[a-zA-Z0-9_]+$", table):
            raise ValidationError("Invalid table name", "table")

        # Validate column names
        if columns:
            for col in columns:
                if not re.match(r"^[a-zA-Z0-9_]+$", col):
                    raise ValidationError(f"Invalid column name: {col}", "columns")
            cols = ", ".join(columns)
        else:
            cols = "*"

        query = f"SELECT {cols} FROM {table}"

        if where_clause:
            query += f" WHERE {where_clause}"

        return query, params or ()

    @staticmethod
    def build_insert(table: str, columns: List[str], values: tuple) -> tuple:
        """
        Build a safe INSERT query with parameterized values

        Args:
            table: Table name (validated)
            columns: List of column names (validated)
            values: Tuple of values to insert

        Returns:
            Tuple of (query_string, values)
        """
        # Validate table name
        if not re.match(r"^[a-zA-Z0-9_]+$", table):
            raise ValidationError("Invalid table name", "table")

        # Validate column names
        for col in columns:
            if not re.match(r"^[a-zA-Z0-9_]+$", col):
                raise ValidationError(f"Invalid column name: {col}", "columns")

        cols = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])

        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

        return query, values

    @staticmethod
    def build_update(
        table: str, set_clause: str, where_clause: str, params: tuple
    ) -> tuple:
        """
        Build a safe UPDATE query with parameterized values

        Args:
            table: Table name (validated)
            set_clause: SET clause with ? placeholders
            where_clause: WHERE clause with ? placeholders
            params: Tuple of parameter values

        Returns:
            Tuple of (query_string, params)
        """
        # Validate table name
        if not re.match(r"^[a-zA-Z0-9_]+$", table):
            raise ValidationError("Invalid table name", "table")

        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        return query, params
