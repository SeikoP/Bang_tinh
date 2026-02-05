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
    """De