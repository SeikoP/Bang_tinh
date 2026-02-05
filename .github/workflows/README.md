# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Warehouse Management System.

## Workflows

### ci-cd.yml
Main CI/CD pipeline that runs on push, pull requests, and releases.

**Jobs:**
- `lint`: Code quality checks (flake8, black, mypy)
- `test`: Run test suite with coverage reporting
- `build`: Build Windows executable (main/develop branches only)
- `release`: Create installer and upload to GitHub Releases (tagged releases only)

**Optimizations:**
- Pip dependency caching for faster installs
- PyInstaller build cache for incremental builds
- Pytest cache for faster test discovery
- Inno Setup cache for release builds
- Parallel job execution where possible

### version.yml
Automated versioning and changelog generation workflow.

**Trigger:** Manual workflow dispatch

**Options:**
- `auto`: Analyze commits and determine version bump automatically
- `major`: Force major version bump (breaking changes)
- `minor`: Force minor version bump (new features)
- `patch`: Force patch version bump (bug fixes)

## Caching Strategy

### Pip Dependencies
- **Key:** `${{ runner.os }}-pip-{job}-${{ hashFiles('**/requirements*.txt') }}`
- **Path:** `~\AppData\Local\pip\Cache`
- **Benefit:** Reduces dependency installation time by ~60%

### PyInstaller Build Cache
- **Key:** `${{ runner.os }}-pyinstaller-${{ hashFiles('warehouse_app.spec') }}`
- **Path:** `build`, `~\AppData\Local\pyinstaller`
- **Benefit:** Speeds up incremental builds by ~40%

### Pytest Cache
- **Key:** `${{ runner.os }}-pytest-${{ github.sha }}`
- **Path:** `.pytest_cache`
- **Benefit:** Faster test discovery and collection

### Inno Setup Cache
- **Key:** `${{ runner.os }}-innosetup-6`
- **Path:** `C:\Program Files (x86)\Inno Setup 6`
- **Benefit:** Avoids reinstalling Inno Setup on every release

## Performance Metrics

Expected workflow execution times:
- Lint job: ~2-3 minutes
- Test job: ~5-7 minutes
- Build job: ~8-10 minutes
- Release job: ~12-15 minutes

Total pipeline time (push to main): ~15-20 minutes
Total pipeline time (release): ~20-25 minutes

## Secrets Required

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `CODECOV_TOKEN`: (Optional) For Codecov integration

## Branch Protection

Recommended branch protection rules for `main`:
- Require status checks to pass before merging
- Require `lint` and `test` jobs to pass
- Require pull request reviews
- Require branches to be up to date before merging

## Usage Examples

### Trigger Manual Version Bump
```bash
# Via GitHub UI: Actions > Version and Changelog > Run workflow
# Select bump type: auto, major, minor, or patch
```

### Create a Release
```bash
# Create and push a tag
git tag -a v2.1.0 -m "Release 2.1.0"
git push origin v2.1.0

# Create release on GitHub
# The release workflow will automatically build and upload assets
```

### View Build Artifacts
Build artifacts are available for 30 days after each build:
1. Go to Actions tab
2. Select the workflow run
3. Download artifacts from the Artifacts section

## Troubleshooting

### Build Fails with "Module not found"
- Check that all dependencies are in `requirements.txt`
- Verify `hiddenimports` in `warehouse_app.spec`

### Tests Fail in CI but Pass Locally
- Check Python version matches (3.11)
- Verify environment variables are set correctly
- Check for platform-specific issues (Windows paths)

### Cache Not Working
- Verify cache key includes correct hash files
- Check cache size limits (10GB per repository)
- Clear cache manually if corrupted: Settings > Actions > Caches

## Maintenance

### Updating Dependencies
When updating dependencies:
1. Update `requirements.txt` or `requirements-dev.txt`
2. Cache keys will automatically update based on file hash
3. First run after update will be slower (cache miss)

### Updating Python Version
1. Update `python-version` in all workflow files
2. Test locally with new version first
3. Update in all jobs consistently

### Monitoring Workflow Performance
- Review workflow run times regularly
- Identify slow steps for optimization
- Consider splitting large jobs into smaller parallel jobs
