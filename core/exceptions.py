"""Custom exception hierarchy for application errors"""


class AppException(Exception):
    """Base exception for application errors"""

    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}


class ValidationError(AppException):
    """Raised when validation fails"""

    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field})


class DatabaseError(AppException):
    """Raised when database operation fails"""

    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation})


class ConfigurationError(AppException):
    """Raised when configuration is invalid"""

    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})


class BusinessRuleError(AppException):
    """Raised when business rule is violated"""

    def __init__(self, message: str, rule: str = None):
        super().__init__(message, "BUSINESS_RULE_ERROR", {"rule": rule})


class SecurityError(AppException):
    """Raised when security violation occurs"""

    def __init__(self, message: str, violation_type: str = None):
        super().__init__(message, "SECURITY_ERROR", {"violation_type": violation_type})
