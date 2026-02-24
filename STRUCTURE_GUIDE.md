# Repository Structure Guide

## Canonical source root
- Use `src/` as the single source of truth for application code.
- Root-level duplicated folders (`core/`, `runtime/`, `services/`, `viewmodels/`, etc.) are legacy and should not be edited for new changes.

## Run behavior
- `main.py` now prioritizes `src/` in `sys.path`, so imports resolve from `src` first.

## Team rules (recommended)
1. New/updated Python modules go under `src/`.
2. New imports should target packages that resolve from `src`.
3. Avoid editing duplicated root modules unless doing a migration cleanup.

## Suggested next cleanup (separate PR)
1. Remove legacy duplicated root folders after verification.
2. Keep only `src/` package tree.
3. Update CI/package scripts to validate `src`-only layout.
