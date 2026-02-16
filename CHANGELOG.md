# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial production-ready refactoring implementation
- Clean architecture with dependency injection
- Comprehensive testing infrastructure
- CI/CD pipeline with GitHub Actions
- Automated build and release system
- Security hardening and license validation
- Database migration system
- Logging and error handling framework

## [2.0.0] - 2025-02-06

### Added
- Complete architectural refactoring to clean architecture
- Dependency injection container for service management
- Configuration management with environment variables
- Comprehensive logging infrastructure with rotation
- Custom exception hierarchy and error handling framework
- Database migration system with up/down support
- Enhanced domain models with validation
- Repository pattern implementation with interfaces
- Service layer with business logic separation
- Security hardening (input validation, license validation)
- PyInstaller build configuration
- Inno Setup installer configuration
- Property-based testing infrastructure
- Unit and integration test suites
- CI/CD pipeline with GitHub Actions
- Automated versioning and changelog generation

### Changed
- Refactored UI layer to use dependency injection
- Extracted business logic from UI components
- Improved database schema with indexes and constraints
- Enhanced error handling with user-friendly messages
- Optimized UI responsiveness with loading indicators

### Security
- Moved sensitive configuration to environment variables
- Implemented input validation framework
- Added SQL injection prevention
- Implemented license key validation system
- Added secure update mechanism with signature verification
- Removed debug code from production builds

## [1.0.0] - 2024-12-01

### Added
- Initial release of WMS
- PyQt6 user interface
- Product catalog management
- Stock tracking and calculation
- Bank notification integration
- Session history tracking
- Export functionality
- SQLite database backend
