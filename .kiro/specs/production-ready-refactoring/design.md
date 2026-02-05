# Design Document: Production-Ready Refactoring

## Overview

This design document outlines the comprehensive transformation of the PyQt6 warehouse management application into a production-ready, commercially distributable system. The design addresses ten major areas: code audit, architectural refactoring, data layer enhancement, UI/UX optimization, Windows build system, testing infrastructure, CI/CD pipeline, security hardening, documentation, and delivery strategy.

The refactoring follows clean architecture principles with clear separation of concerns across five layers: UI (PyQt6 views), Core (business logic), Service (application services), Data (repositories and models), and Utils (shared utilities). The design emphasizes testability, maintainability, security, and commercial distribution readiness.

## Architecture

### Current Architecture Analysis

The existing application has the following structure:

```
main.py (1000+ lines)
├── UI Components (QMainWindow, Views)
├── HTTP Server (NotificationServer)
├── Business Logic (mixed with UI)
└── Direct Database Calls

database/
├── connection.py (SQLite connection)
├── models.py (Dataclasses)
└── repositories.py (CRUD operations)

services/
├── calculator.py (Business logic)
├── exporter.py (Export functionality)
└── report_service.py (Reporting)

ui/
├── qt_theme.py (Styling)
└── qt_views/ (View components)
```

**Identified Issues:**
- Tight coupling between UI and business logic
- Main.py contains multiple responsibilities (UI, server, notifications)
- No dependency injection framework
- Configuration mixed with code
- No interface abstractions
- Limited error handling
- No logging infrastructure
- Security concerns (hardcoded port, no authentication)

### Target Architecture

The refactored architecture implements clean architecture with dependency inversion:

```
┌─────────────────────────────────────────────────────────┐
│                     UI Layer (PyQt6)                     │
│  MainWindow, Views, Dialogs, Widgets                    │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
┌────────────────────▼────────────────────────────────────┐
│                    Core Layer                            │
│  Interfaces, DTOs, Domain Models, Use Cases             │
└────────────────────┬────────────────────────────────────┘
                     │ implemented by
┌────────────────────▼────────────────────────────────────┐
│                  Service Layer                           │
│  CalculatorService, ExportService, NotificationService  │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
┌────────────────────▼────────────────────────────────────┐
│                   Data Layer                             │
│  Repositories, Database Connection, Migrations          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Utils Layer                            │
│  Formatters, Validators, Logging, Configuration         │
└─────────────────────────────────────────────────────────┘
```

**Layer Responsibilities:**

1. **UI Layer**: Presentation logic only, delegates all business operations to Core
2. **Core Layer**: Business rules, use cases, domain models, interfaces
3. **Service Layer**: Application services implementing core interfaces
4. **Data Layer**: Data access, persistence, external integrations
5. **Utils Layer**: Cross-cutting concerns (logging, config, validation)

## Components and Interfaces

### 1. Dependency Injection Container

```python
# core/container.py
class Container:
    """Dependency injection container"""
    
    def __init__(self, config: Config):
        self._config = config
        self._services = {}
        self._register_services()
    
    def _register_services(self):
        # Register singletons
        self._services['database'] = DatabaseConnection(self._config.db_path)
        self._services['logger'] = LoggerFactory.create(self._config.log_level)
        
        # Register repositories
        self._services['product_repo'] = ProductRepository(self.get('database'))
        self._services['session_repo'] = SessionRepository(self.get('database'))
        
        # Register services
        self._services['calculator'] = CalculatorService()
        self._services['exporter'] = ExportService(self._config.export_dir)
        self._services['notification'] = NotificationService(
            self.get('logger'),
            self._config.notification_port
        )
    
    def get(self, service_name: str):
        return self._services.get(service_name)
```

### 2. Configuration Management

```python
# core/config.py
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Optional

@dataclass
class Config:
    """Application configuration"""
    
    # Paths
    base_dir: Path
    db_path: Path
    export_dir: Path
    backup_dir: Path
    log_dir: Path
    
    # Application
    app_name: str
    app_version: str
    environment: str  # dev, staging, production
    
    # UI
    window_width: int
    window_height: int
    theme: str
    
    # Server
    notification_port: int
    notification_host: str
    enable_ssl: bool
    
    # Security
    license_key: Optional[str]
    encryption_key: Optional[str]
    
    # Logging
    log_level: str
    log_rotation: str
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        base_dir = Path(os.getenv('APP_BASE_DIR', Path.cwd()))
        
        return cls(
            base_dir=base_dir,
            db_path=Path(os.getenv('DB_PATH', base_dir / 'storage.db')),
            export_dir=Path(os.getenv('EXPORT_DIR', base_dir / 'exports')),
            backup_dir=Path(os.getenv('BACKUP_DIR', base_dir / 'backups')),
            log_dir=Path(os.getenv('LOG_DIR', base_dir / 'logs')),
            app_name=os.getenv('APP_NAME', 'Warehouse Management'),
            app_version=os.getenv('APP_VERSION', '2.0.0'),
            environment=os.getenv('ENVIRONMENT', 'production'),
            window_width=int(os.getenv('WINDOW_WIDTH', '1200')),
            window_height=int(os.getenv('WINDOW_HEIGHT', '800')),
            theme=os.getenv('THEME', 'modern'),
            notification_port=int(os.getenv('NOTIFICATION_PORT', '5005')),
            notification_host=os.getenv('NOTIFICATION_HOST', '0.0.0.0'),
            enable_ssl=os.getenv('ENABLE_SSL', 'false').lower() == 'true',
            license_key=os.getenv('LICENSE_KEY'),
            encryption_key=os.getenv('ENCRYPTION_KEY'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_rotation=os.getenv('LOG_ROTATION', 'daily'),
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.db_path.parent.exists():
            errors.append(f"Database directory does not exist: {self.db_path.parent}")
        
        if self.notification_port < 1024 or self.notification_port > 65535:
            errors.append(f"Invalid notification port: {self.notification_port}")
        
        if self.environment == 'production' and not self.license_key:
            errors.append("License key required for production environment")
        
        return errors
```

### 3. Core Interfaces

```python
# core/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

class IProductRepository(ABC):
    """Interface for product data access"""
    
    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List['Product']:
        pass
    
    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional['Product']:
        pass
    
    @abstractmethod
    def add(self, product: 'Product') -> int:
        pass
    
    @abstractmethod
    def update(self, product: 'Product') -> bool:
        pass
    
    @abstractmethod
    def delete(self, product_id: int) -> bool:
        pass

class ICalculatorService(ABC):
    """Interface for calculation business logic"""
    
    @abstractmethod
    def parse_to_small_units(self, value_str: str, conversion: int) -> int:
        pass
    
    @abstractmethod
    def format_to_display(self, total_small_units: int, conversion: int, unit_char: str) -> str:
        pass
    
    @abstractmethod
    def calculate_session_total(self) -> float:
        pass

class INotificationService(ABC):
    """Interface for notification handling"""
    
    @abstractmethod
    def start_server(self) -> None:
        pass
    
    @abstractmethod
    def stop_server(self) -> None:
        pass
    
    @abstractmethod
    def register_handler(self, handler: callable) -> None:
        pass
```

### 4. Logging Infrastructure

```python
# utils/logging.py
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

class LoggerFactory:
    """Factory for creating configured loggers"""
    
    @staticmethod
    def create(
        name: str,
        log_dir: Path,
        level: str = 'INFO',
        rotation: str = 'daily',
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """Create a configured logger"""
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f'{name}.log'
        
        if rotation == 'size':
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
        else:  # daily rotation
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=backup_count
            )
        
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
```

### 5. Error Handling Framework

```python
# core/exceptions.py
class AppException(Exception):
    """Base exception for application errors"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or 'UNKNOWN_ERROR'
        self.details = details or {}

class ValidationError(AppException):
    """Raised when validation fails"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, 'VALIDATION_ERROR', {'field': field})

class DatabaseError(AppException):
    """Raised when database operation fails"""
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, 'DATABASE_ERROR', {'operation': operation})

class ConfigurationError(AppException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, 'CONFIG_ERROR', {'config_key': config_key})

# utils/error_handler.py
from PyQt6.QtWidgets import QMessageBox
import logging

class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def handle(self, error: Exception, parent_widget=None) -> None:
        """Handle an error with logging and user notification"""
        
        if isinstance(error, AppException):
            self.logger.error(
                f"{error.code}: {error.message}",
                extra={'details': error.details}
            )
            self._show_user_message(error.message, parent_widget)
        else:
            self.logger.exception("Unexpected error occurred")
            self._show_user_message(
                "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.",
                parent_widget
            )
    
    def _show_user_message(self, message: str, parent=None):
        """Show error message to user"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Lỗi")
        msg_box.exec()
```

### 6. Database Migration System

```python
# database/migrations.py
from abc import ABC, abstractmethod
from typing import List
import sqlite3
from pathlib import Path

class Migration(ABC):
    """Base class for database migrations"""
    
    @property
    @abstractmethod
    def version(self) -> int:
        """Migration version number"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Migration description"""
        pass
    
    @abstractmethod
    def up(self, conn: sqlite3.Connection) -> None:
        """Apply migration"""
        pass
    
    @abstractmethod
    def down(self, conn: sqlite3.Connection) -> None:
        """Rollback migration"""
        pass

class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db_path: Path, migrations: List[Migration]):
        self.db_path = db_path
        self.migrations = sorted(migrations, key=lambda m: m.version)
    
    def get_current_version(self) -> int:
        """Get current database version"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
    
    def migrate(self, target_version: int = None) -> None:
        """Apply migrations up to target version"""
        current = self.get_current_version()
        target = target_version or self.migrations[-1].version
        
        if current >= target:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for migration in self.migrations:
                if current < migration.version <= target:
                    print(f"Applying migration {migration.version}: {migration.description}")
                    migration.up(conn)
                    conn.execute(
                        "INSERT INTO schema_version (version) VALUES (?)",
                        (migration.version,)
                    )
                    conn.commit()
```

## Data Models

### Enhanced Data Models with Validation

```python
# core/models.py
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

@dataclass
class Product:
    """Product domain model with validation"""
    id: Optional[int]
    name: str
    large_unit: str
    conversion: int
    unit_price: Decimal
    is_active: bool = True
    is_favorite: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        self.validate()
    
    def validate(self) -> None:
        """Validate product data"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValidationError("Product name cannot be empty", "name")
        
        if self.conversion <= 0:
            raise ValidationError("Conversion must be positive", "conversion")
        
        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative", "unit_price")
        
        if len(self.name) > 200:
            raise ValidationError("Product name too long (max 200 characters)", "name")
    
    @property
    def unit_char(self) -> str:
        """Get unit abbreviation"""
        mapping = {
            "Thùng": "t", "Vỉ": "v", "Gói": "g",
            "Két": "k", "Hộp": "h", "Chai": "c",
        }
        return mapping.get(self.large_unit, self.large_unit[0].lower())

@dataclass
class SessionData:
    """Session data with business rules"""
    product: Product
    handover_qty: int = 0
    closing_qty: int = 0
    
    def __post_init__(self):
        self.validate()
    
    def validate(self) -> None:
        """Validate session data"""
        if self.handover_qty < 0:
            raise ValidationError("Handover quantity cannot be negative", "handover_qty")
        
        if self.closing_qty < 0:
            raise ValidationError("Closing quantity cannot be negative", "closing_qty")
        
        if self.closing_qty > self.handover_qty:
            raise ValidationError("Closing quantity cannot exceed handover quantity", "closing_qty")
    
    @property
    def used_qty(self) -> int:
        """Calculate used quantity"""
        return max(0, self.handover_qty - self.closing_qty)
    
    @property
    def amount(self) -> Decimal:
        """Calculate amount"""
        return Decimal(self.used_qty) * self.product.unit_price
```

### Database Schema Enhancements

```sql
-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_session_history_date ON session_history(session_date);
CREATE INDEX IF NOT EXISTS idx_bank_history_created ON bank_history(created_at);

-- Add foreign key constraints
PRAGMA foreign_keys = ON;

-- Add audit columns to all tables
ALTER TABLE products ADD COLUMN created_by TEXT;
ALTER TABLE products ADD COLUMN updated_by TEXT;

-- Add soft delete support
ALTER TABLE session_history ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE session_history_items ADD COLUMN deleted_at TIMESTAMP;

-- Add data validation constraints
ALTER TABLE products ADD CONSTRAINT chk_conversion_positive CHECK (conversion > 0);
ALTER TABLE products ADD CONSTRAINT chk_price_non_negative CHECK (unit_price >= 0);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Complete File Discovery
*For any* project directory structure, the audit module should discover all Python source files without missing any .py files in the tree.
**Validates: Requirements 1.1**

### Property 2: Architectural Violation Detection
*For any* code sample with known tight coupling patterns (UI importing from Data layer, circular dependencies), the audit module should detect and report these violations.
**Validates: Requirements 1.2**

### Property 3: Code Smell Detection Completeness
*For any* code containing known smells (duplicated blocks, methods exceeding complexity threshold, long parameter lists), the audit module should identify all instances.
**Validates: Requirements 1.3**

### Property 4: Security Vulnerability Detection
*For any* code containing security issues (hardcoded credentials, SQL injection vulnerabilities, missing input validation), the audit module should detect and classify them correctly.
**Validates: Requirements 1.4**

### Property 5: Risk Classification Consistency
*For any* audit finding, it should be assigned exactly one risk level from the valid set {Low, Medium, High, Critical} based on consistent criteria.
**Validates: Requirements 1.6**

### Property 6: Layer Dependency Rules
*For any* import statement in the UI layer, it should only reference modules from the Core layer, never directly from Service or Data layers.
**Validates: Requirements 2.2**

### Property 7: Dependency Injection Pattern
*For any* service class, all external dependencies should be passed through constructor parameters, not instantiated internally.
**Validates: Requirements 2.5**

### Property 8: Configuration Validation Completeness
*For any* configuration object, if required fields are missing or invalid, the validation method should return a non-empty list of errors.
**Validates: Requirements 2.7**

### Property 9: Cyclomatic Complexity Threshold
*For any* method in the refactored codebase, its cyclomatic complexity should be less than 10.
**Validates: Requirements 2.8**

### Property 10: Foreign Key Constraint Completeness
*For any* database relationship between tables, there should exist a corresponding foreign key constraint in the schema.
**Validates: Requirements 3.2**

### Property 11: Migration Bidirectionality
*For any* database migration, it should implement both up() and down() methods that are inverse operations.
**Validates: Requirements 3.4**

### Property 12: Data Preservation During Migration
*For any* test dataset, applying a migration up() then down() should preserve all original data without loss or corruption.
**Validates: Requirements 3.5**

### Property 13: SQL Injection Prevention
*For any* SQL injection payload from a standard attack list, the input validation should reject it before database execution.
**Validates: Requirements 3.7**

### Property 14: Transaction Atomicity
*For any* multi-step database transaction, if any step fails, all changes should be rolled back leaving the database in its original state.
**Validates: Requirements 3.9**

### Property 15: Layout Responsiveness
*For any* window resize operation within valid bounds, all UI layouts should maintain proper proportions without element overlap or truncation.
**Validates: Requirements 4.2**

### Property 16: Action Idempotency During Loading
*For any* action triggered while data is loading, subsequent triggers should be ignored until the first operation completes.
**Validates: Requirements 4.7**

### Property 17: Update Security Verification
*For any* update package, the system should verify cryptographic signatures before applying, rejecting unsigned or tampered packages.
**Validates: Requirements 5.10**

### Property 18: Test Coverage for Business Logic
*For any* business logic class, there should exist at least one corresponding test file with test methods.
**Validates: Requirements 6.1**

### Property 19: Property Test Coverage for Transformations
*For any* data transformation function, there should exist at least one property-based test validating its behavior.
**Validates: Requirements 6.2**

### Property 20: Property Test Iteration Count
*For any* property-based test, it should be configured to run at least 100 iterations.
**Validates: Requirements 6.3**

### Property 21: Secrets in Environment Variables
*For any* sensitive configuration value (passwords, API keys, encryption keys), it should be loaded from environment variables, not hardcoded in source files.
**Validates: Requirements 8.1**

### Property 22: Encryption Algorithm Standards
*For any* encryption operation, the algorithm used should be from the approved list (AES-256-GCM, ChaCha20-Poly1305).
**Validates: Requirements 8.2**

### Property 23: Input Validation Coverage
*For any* user input entry point (form fields, API endpoints, file uploads), there should exist validation logic that executes before processing.
**Validates: Requirements 8.3**

### Property 24: HTTP Request Validation
*For any* HTTP request to the notification server, the system should validate content-type, origin, and payload structure before processing.
**Validates: Requirements 8.4**

### Property 25: License Key Validation
*For any* license key string, the validation function should correctly identify valid keys (proper format, valid signature) and reject invalid ones.
**Validates: Requirements 8.9**

## Error Handling

### Error Handling Strategy

The application implements a comprehensive error handling strategy with three layers:

1. **Domain Layer**: Business rule violations throw typed exceptions (ValidationError, BusinessRuleError)
2. **Application Layer**: Service errors throw application exceptions (DatabaseError, ConfigurationError)
3. **Presentation Layer**: UI catches all exceptions and presents user-friendly messages

### Error Categories

**Validation Errors**:
- User input validation failures
- Data model constraint violations
- Configuration validation errors
- Handled at the point of entry with immediate feedback

**Business Logic Errors**:
- Business rule violations (e.g., closing qty > handover qty)
- State transition errors
- Calculation errors
- Logged and presented to user with corrective actions

**Infrastructure Errors**:
- Database connection failures
- File system errors
- Network errors (notification server)
- Logged with full stack trace, user sees generic error message

**Security Errors**:
- Authentication failures
- Authorization violations
- License validation failures
- Logged as security events, user sees access denied message

### Error Recovery Strategies

**Transient Errors** (network, database locks):
- Automatic retry with exponential backoff
- Maximum 3 retry attempts
- User notification after final failure

**Permanent Errors** (validation, business rules):
- No retry
- Immediate user feedback
- Suggest corrective action

**Critical Errors** (database corruption, configuration missing):
- Application shutdown with error dialog
- Error logged to file
- User directed to support

### Logging Strategy

**Log Levels**:
- DEBUG: Detailed diagnostic information (development only)
- INFO: General informational messages (startup, shutdown, major operations)
- WARNING: Unexpected situations that don't prevent operation
- ERROR: Error events that might still allow operation to continue
- CRITICAL: Serious errors that may cause application termination

**Log Rotation**:
- Daily rotation by default
- Keep 5 days of logs
- Maximum 10MB per log file
- Compressed archives for older logs

**Structured Logging**:
```python
logger.info(
    "Product created",
    extra={
        'product_id': product.id,
        'product_name': product.name,
        'user': current_user,
        'timestamp': datetime.now().isoformat()
    }
)
```

## Testing Strategy

### Testing Pyramid

The testing strategy follows the testing pyramid with emphasis on property-based testing:

```
        /\
       /  \      E2E Tests (5%)
      /    \     - Critical user workflows
     /------\    - Smoke tests
    /        \   
   /  Integ.  \  Integration Tests (15%)
  /   Tests    \ - Database operations
 /--------------\- Service interactions
/                \
/   Unit Tests    \ Unit & Property Tests (80%)
/   Property Tests \ - Business logic
-------------------  - Data transformations
```

### Unit Testing

**Coverage Requirements**:
- Minimum 80% code coverage for business logic
- 100% coverage for critical paths (calculations, data validation)
- Exclude UI code from coverage requirements

**Test Organization**:
```
tests/
├── unit/
│   ├── test_calculator_service.py
│   ├── test_product_model.py
│   ├── test_session_data.py
│   └── test_validators.py
├── integration/
│   ├── test_repositories.py
│   ├── test_database_migrations.py
│   └── test_notification_server.py
├── property/
│   ├── test_calculator_properties.py
│   ├── test_validation_properties.py
│   └── test_migration_properties.py
└── e2e/
    ├── test_calculation_workflow.py
    └── test_product_management.py
```

**Test Fixtures**:
```python
# tests/conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def test_db():
    """Create temporary test database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # Initialize schema
    init_db(db_path)
    
    yield db_path
    
    # Cleanup
    db_path.unlink()

@pytest.fixture
def sample_products():
    """Create sample products for testing"""
    return [
        Product(id=1, name="Product A", large_unit="Thùng", 
                conversion=24, unit_price=Decimal("10.50")),
        Product(id=2, name="Product B", large_unit="Vỉ", 
                conversion=10, unit_price=Decimal("5.00")),
    ]
```

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Property Test Configuration**:
```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=100, deadline=None)
@given(
    value_str=st.text(min_size=1, max_size=10),
    conversion=st.integers(min_value=1, max_value=100)
)
def test_parse_to_small_units_property(value_str, conversion):
    """
    Feature: production-ready-refactoring
    Property 1: Parse then format round trip
    
    For any valid input string and conversion factor,
    parsing then formatting should preserve the value
    """
    calculator = CalculatorService()
    
    # Parse to small units
    small_units = calculator.parse_to_small_units(value_str, conversion)
    
    # Format back to display
    formatted = calculator.format_to_display(small_units, conversion, 't')
    
    # Parse again
    reparsed = calculator.parse_to_small_units(formatted, conversion)
    
    # Should be equal (round trip property)
    assert small_units == reparsed
```

**Property Test Examples**:

1. **Calculator Round Trip**:
   - For any input, parse → format → parse should return original value
   - Validates: Parsing and formatting are inverse operations

2. **Validation Consistency**:
   - For any invalid input, validation should always reject it
   - For any valid input, validation should always accept it
   - Validates: Validation logic is deterministic

3. **Migration Bidirectionality**:
   - For any migration, up() then down() should restore original state
   - Validates: Migrations are reversible

4. **Transaction Atomicity**:
   - For any multi-step transaction with forced failure, no partial changes persist
   - Validates: Database transactions are atomic

5. **Input Sanitization**:
   - For any SQL injection payload, sanitization should neutralize it
   - Validates: Security input validation

### Integration Testing

**Database Integration Tests**:
```python
def test_product_repository_crud(test_db):
    """Test complete CRUD cycle for products"""
    repo = ProductRepository(test_db)
    
    # Create
    product = Product(
        id=None,
        name="Test Product",
        large_unit="Thùng",
        conversion=24,
        unit_price=Decimal("10.00")
    )
    product_id = repo.add(product)
    assert product_id > 0
    
    # Read
    retrieved = repo.get_by_id(product_id)
    assert retrieved.name == "Test Product"
    
    # Update
    retrieved.unit_price = Decimal("12.00")
    assert repo.update(retrieved)
    
    # Delete
    assert repo.delete(product_id)
    assert repo.get_by_id(product_id) is None
```

**Service Integration Tests**:
```python
def test_notification_service_integration(test_config):
    """Test notification server receives and processes messages"""
    service = NotificationService(test_config)
    received_messages = []
    
    def handler(message):
        received_messages.append(message)
    
    service.register_handler(handler)
    service.start_server()
    
    # Send test notification
    response = requests.post(
        f"http://localhost:{test_config.notification_port}",
        json={"content": "Test message"}
    )
    
    assert response.status_code == 200
    time.sleep(0.1)  # Allow processing
    assert len(received_messages) == 1
    assert received_messages[0] == "Test message"
    
    service.stop_server()
```

### End-to-End Testing

**Smoke Tests**:
```python
def test_application_startup(qtbot):
    """Test application starts without errors"""
    app = QApplication([])
    window = MainWindow()
    window.show()
    qtbot.addWidget(window)
    
    # Verify main components loaded
    assert window.calc_view is not None
    assert window.stock_view is not None
    assert window.product_view is not None
    
    window.close()
```

**Critical Workflow Tests**:
```python
def test_calculation_workflow(qtbot, test_db):
    """Test complete calculation workflow"""
    app = QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Navigate to calculation view
    window._switch_view(0)
    
    # Enter handover quantity
    calc_view = window.calc_view
    calc_view.table.item(0, 1).setText("3.5")
    
    # Enter closing quantity
    calc_view.table.item(0, 2).setText("1.2")
    
    # Verify calculation
    used_item = calc_view.table.item(0, 3)
    assert used_item.text() == "2.3"
    
    # Save session
    calc_view.save_session()
    
    # Verify saved to history
    history = HistoryRepository.get_all()
    assert len(history) > 0
```

### Test Automation

**Continuous Integration**:
- All tests run on every push
- Pull requests require passing tests
- Coverage reports generated automatically
- Failed tests block merges

**Test Execution**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=xml

# Run only unit tests
pytest tests/unit/

# Run only property tests
pytest tests/property/ -v

# Run with specific markers
pytest -m "not slow"
```

**Performance Testing**:
- Benchmark critical operations (calculation, database queries)
- Fail if performance degrades by >20%
- Track performance trends over time

### Test Data Management

**Test Data Generators**:
```python
from hypothesis import strategies as st

# Product generator
product_strategy = st.builds(
    Product,
    id=st.integers(min_value=1),
    name=st.text(min_size=1, max_size=200),
    large_unit=st.sampled_from(["Thùng", "Vỉ", "Gói", "Két"]),
    conversion=st.integers(min_value=1, max_value=100),
    unit_price=st.decimals(min_value=0, max_value=1000, places=2)
)

# Session data generator
session_strategy = st.builds(
    SessionData,
    product=product_strategy,
    handover_qty=st.integers(min_value=0, max_value=1000),
    closing_qty=st.integers(min_value=0, max_value=1000)
).filter(lambda s: s.closing_qty <= s.handover_qty)
```

## Build System Configuration

### Tool Selection: PyInstaller

After evaluation, PyInstaller is selected for the following reasons:
- Mature and widely used in production
- Excellent PyQt6 support
- Single-file executable support
- Cross-platform compatibility
- Active community and documentation

**Alternative Considered**:
- Nuitka: Better performance but longer build times, complexity
- cx_Freeze: Less mature PyQt6 support

### PyInstaller Configuration

**Spec File** (warehouse_app.spec):
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('config.py', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sqlite3',
        'logging.handlers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WarehouseManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='version_info.txt',
)
```

**Version Info** (version_info.txt):
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 0, 0),
    prodvers=(2, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Bangla Team'),
        StringStruct(u'FileDescription', u'Warehouse Management System'),
        StringStruct(u'FileVersion', u'2.0.0.0'),
        StringStruct(u'InternalName', u'WarehouseManagement'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
        StringStruct(u'OriginalFilename', u'WarehouseManagement.exe'),
        StringStruct(u'ProductName', u'Warehouse Management'),
        StringStruct(u'ProductVersion', u'2.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

### Build Scripts

**Build Script** (scripts/build.py):
```python
#!/usr/bin/env python
"""Build script for creating Windows executable"""

import subprocess
import shutil
from pathlib import Path
import sys

def clean_build_dirs():
    """Remove previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name}/")

def build_executable():
    """Build executable using PyInstaller"""
    print("Building executable...")
    result = subprocess.run(
        ['pyinstaller', 'warehouse_app.spec', '--clean'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Build failed:")
        print(result.stderr)
        sys.exit(1)
    
    print("Build successful!")
    print(f"Executable: dist/WarehouseManagement.exe")

def create_installer():
    """Create MSI installer using WiX or Inno Setup"""
    print("Creating installer...")
    # Use Inno Setup for installer creation
    subprocess.run([
        'iscc',
        'installer/setup.iss'
    ])

if __name__ == '__main__':
    clean_build_dirs()
    build_executable()
    create_installer()
```

### Installer Configuration

**Inno Setup Script** (installer/setup.iss):
```ini
[Setup]
AppName=Warehouse Management
AppVersion=2.0.0
DefaultDirName={pf}\WarehouseManagement
DefaultGroupName=Warehouse Management
OutputDir=dist
OutputBaseFilename=WarehouseManagement-Setup-2.0.0
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=..\assets\icon.ico
WizardStyle=modern

[Files]
Source: "..\dist\WarehouseManagement.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Warehouse Management"; Filename: "{app}\WarehouseManagement.exe"
Name: "{commondesktop}\Warehouse Management"; Filename: "{app}\WarehouseManagement.exe"

[Run]
Filename: "{app}\WarehouseManagement.exe"; Description: "Launch Warehouse Management"; Flags: postinstall nowait skipifsilent
```

## CI/CD Pipeline

### GitHub Actions Workflow

**Main Workflow** (.github/workflows/ci-cd.yml):
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ created ]

jobs:
  lint:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black mypy
      
      - name: Run linters
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          black --check .
          mypy . --ignore-missing-imports

  test:
    runs-on: windows-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-qt hypothesis
      
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  build:
    runs-on: windows-latest
    needs: test
    if: github.event_name == 'push' || github.event_name == 'release'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: |
          python scripts/build.py
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: WarehouseManagement-Windows
          path: dist/WarehouseManagement.exe

  release:
    runs-on: windows-latest
    needs: build
    if: github.event_name == 'release'
    steps:
      - uses: actions/checkout@v3
      
      - name: Download artifact
        uses: actions/download-artifact@v3
        with:
          name: WarehouseManagement-Windows
      
      - name: Create installer
        run: |
          choco install innosetup -y
          iscc installer/setup.iss
      
      - name: Upload release assets
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/WarehouseManagement-Setup-*.exe
            dist/WarehouseManagement.exe
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Security Hardening Implementation

**Environment Variables** (.env.example):
```ini
# Application Configuration
APP_NAME=Warehouse Management
APP_VERSION=2.0.0
ENVIRONMENT=production

# Database
DB_PATH=storage.db

# Server
NOTIFICATION_PORT=5005
NOTIFICATION_HOST=0.0.0.0
ENABLE_SSL=false

# Security
LICENSE_KEY=
ENCRYPTION_KEY=

# Logging
LOG_LEVEL=INFO
LOG_ROTATION=daily
```

**License Validation** (core/license.py):
```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
import base64
import json

class LicenseValidator:
    """Validates application license keys"""
    
    def __init__(self, public_key_pem: str):
        self.public_key = serialization.load_pem_public_key(
            public_key_pem.encode()
        )
    
    def validate(self, license_key: str) -> tuple[bool, dict]:
        """
        Validate license key
        Returns: (is_valid, license_data)
        """
        try:
            # Decode license key
            parts = license_key.split('.')
            if len(parts) != 2:
                return False, {}
            
            payload_b64, signature_b64 = parts
            payload = base64.b64decode(payload_b64)
            signature = base64.b64decode(signature_b64)
            
            # Verify signature
            self.public_key.verify(
                signature,
                payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Parse license data
            license_data = json.loads(payload.decode())
            
            # Check expiration
            from datetime import datetime
            expiry = datetime.fromisoformat(license_data.get('expiry'))
            if datetime.now() > expiry:
                return False, {}
            
            return True, license_data
            
        except (InvalidSignature, ValueError, KeyError):
            return False, {}
```

This completes the design document with comprehensive coverage of all ten major areas of the production-ready refactoring project.
