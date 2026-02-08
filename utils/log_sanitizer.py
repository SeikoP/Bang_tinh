"""
Log Sanitization - Remove sensitive data from logs
"""

import re
from typing import Any, Dict


class LogSanitizer:
    """Sanitize sensitive data from logs"""
    
    # Patterns to detect sensitive data
    PATTERNS = {
        'api_key': re.compile(r'(api[_-]?key|apikey|token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', re.IGNORECASE),
        'password': re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)', re.IGNORECASE),
        'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        'phone': re.compile(r'\b0\d{9,10}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'bank_account': re.compile(r'\b\d{10,16}\b'),
    }
    
    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """
        Sanitize sensitive data from string
        
        Args:
            text: Input string
            
        Returns:
            Sanitized string
        """
        if not text:
            return text
        
        result = text
        
        # Replace API keys
        result = cls.PATTERNS['api_key'].sub(r'\1=***REDACTED***', result)
        
        # Replace passwords
        result = cls.PATTERNS['password'].sub(r'\1=***REDACTED***', result)
        
        # Replace credit cards
        result = cls.PATTERNS['credit_card'].sub('****-****-****-****', result)
        
        # Partially mask phone numbers
        result = cls.PATTERNS['phone'].sub(lambda m: m.group(0)[:3] + '****' + m.group(0)[-3:], result)
        
        # Partially mask emails
        result = cls.PATTERNS['email'].sub(
            lambda m: m.group(0).split('@')[0][:2] + '***@' + m.group(0).split('@')[1],
            result
        )
        
        # Partially mask bank accounts
        result = cls.PATTERNS['bank_account'].sub(lambda m: '****' + m.group(0)[-4:], result)
        
        return result
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data from dictionary
        
        Args:
            data: Input dictionary
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = {
            'password', 'passwd', 'pwd', 'secret', 'token',
            'api_key', 'apikey', 'private_key', 'access_token',
            'refresh_token', 'auth_token', 'session_id'
        }
        
        result = {}
        for key, value in data.items():
            # Check if key is sensitive
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                result[key] = '***REDACTED***'
            elif isinstance(value, str):
                result[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                result[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    cls.sanitize_dict(item) if isinstance(item, dict)
                    else cls.sanitize_string(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    @classmethod
    def sanitize_exception(cls, exc: Exception) -> str:
        """
        Sanitize exception message
        
        Args:
            exc: Exception object
            
        Returns:
            Sanitized exception string
        """
        exc_str = str(exc)
        return cls.sanitize_string(exc_str)


# Example usage in logging
import logging

class SanitizingFormatter(logging.Formatter):
    """Logging formatter that sanitizes sensitive data"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Sanitize message
        if isinstance(record.msg, str):
            record.msg = LogSanitizer.sanitize_string(record.msg)
        
        # Sanitize args
        if record.args:
            record.args = tuple(
                LogSanitizer.sanitize_string(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        # Sanitize exception info
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_value:
                sanitized_msg = LogSanitizer.sanitize_exception(exc_value)
                record.exc_info = (exc_type, Exception(sanitized_msg), exc_tb)
        
        return super().format(record)


# Update utils/logging.py to use sanitizing formatter
def create_sanitizing_logger(name: str, log_dir, level, rotation):
    """Create logger with sanitization"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # File handler with sanitization
    log_file = log_dir / f"{name}.log"
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Use sanitizing formatter
    formatter = SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
