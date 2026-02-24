# WMS — Warehouse Management System

A professional desktop warehouse management application built with **PyQt6** and **Python 3.11+**.

Manages product inventory, calculates stock usage, processes bank notifications, and generates PDF/Excel reports — all from a single standalone Windows application.

---

## Features

- **Stock Management** — Track products with large/small unit conversion (thùng→lon, vỉ→gói, etc.)
- **Session Tracking** — Handover vs. closing quantities with automatic "used" calculation
- **Bank Notification Integration** — Real-time HTTP server (port 5005) receives alerts from the Android companion app
- **Reports & Export** — PDF and Excel reports with Vietnamese formatting
- **QR Code** — Generate QR codes for product lookups
- **Text-to-Speech** — Read bank notifications aloud via Edge TTS
- **License Validation** — RSA-signed offline license system
- **Auto-Backup** — Scheduled SQLite database backups

## Architecture

```
bang_tinh/
├── src/wms/                  # Main application package
│   ├── __main__.py           # Entry point (python -m wms)
│   ├── core/                 # Config, constants, DI container, interfaces
│   ├── database/             # SQLite connection pool, repositories, migrations
│   ├── services/             # Business logic (calculator, bank parser, AI, TTS)
│   ├── ui/                   # PyQt6 windows, views, widgets, themes
│   ├── runtime/              # Bootstrap, lifecycle, crash handler, watchdog
│   ├── network/              # HTTP notification server & handler
│   ├── workers/              # Background QThread workers
│   ├── utils/                # Logging, formatters, validators, error handler
│   ├── audit/                # Code quality & security analyzers
│   └── assets/               # Icons, images
├── tests/                    # pytest test suite (unit, integration, property, e2e, security)
├── config/                   # YAML configuration files
├── build/                    # PyInstaller spec, Inno Setup installer, version info
├── android_notifier/         # Companion Android app (git submodule)
├── data/                     # Runtime data (logs, exports, backups, cache)
├── archive/                  # Legacy/deprecated code (preserved for reference)
├── pyproject.toml            # Package metadata, dependencies, tool config
└── .github/workflows/        # CI/CD pipeline (lint → test → build → release)
```

**Key patterns:**
- **Dependency Injection** — `core/container.py` registers all singletons
- **Repository Pattern** — `database/repositories.py` for all data access
- **Bootstrap → Lifecycle** — `runtime/bootstrap.py` initializes, `runtime/lifecycle.py` runs the event loop
- **Worker Threads** — `QThread`-based workers for background operations

## Quick Start

### Prerequisites

- Python 3.11+
- Windows 10/11

### Setup

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/SeikoP/Bang_tinh.git
cd Bang_tinh

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install in development mode
pip install -e .

# Copy and configure environment
copy .env.example .env
```

### Run

```bash
# Run the application
python -m wms

# Or use the console script
wms
```

### Test

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=wms --cov-report=term
```

### Build Executable

```bash
pip install pyinstaller
pyinstaller build/warehouse_app.spec
# Output: dist/WarehouseManagement.exe
```

## Configuration

| File | Purpose |
|------|---------|
| `.env` | Environment variables (DB path, ports, keys) |
| `config/app.yaml` | Application settings |
| `config/logging.yaml` | Logging configuration |
| `config/paths.yaml` | Path overrides |

## License

See [LICENSE.txt](LICENSE.txt).
