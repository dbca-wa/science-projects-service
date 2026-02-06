# GitHub Actions Workflows

## Overview

Three workflows automate testing, building, and releasing the backend service:

1. **test.yml** - Runs on every push/PR to main/develop
2. **build.yml** - Builds Docker image after tests pass on main
3. **release.yml** - Publishes Docker image when version tags are pushed

## Workflows

### 1. Test Suite (`test.yml`)

**Triggers:**
- Push to `main` or `develop` branches (backend changes only)
- Pull requests to `main` or `develop` (backend changes only)

**What it does:**
- Runs full test suite with pytest
- Generates coverage report (minimum 80%)
- Uploads coverage to Codecov
- Creates coverage badge on `main` branch

**Execution time:** ~4 minutes (with parallel testing)

**Key features:**
- Parallel test execution (`-n auto` uses all 4 CPU cores)
- PostgreSQL 17 service container
- Coverage badge generation
- Artifact upload (HTML coverage report, 30-day retention)

### 2. Build Docker Image (`build.yml`)

**Triggers:**
- After `test.yml` completes successfully on `main` branch

**What it does:**
- Builds Docker image (does NOT push to registry)
- Validates Dockerfile and build process
- Uses build cache for faster builds

**Execution time:** ~2-3 minutes

**Key features:**
- Only runs if tests pass
- Uses Docker layer caching
- Tags image but doesn't publish (release workflow handles publishing)

### 3. Release (`release.yml`)

**Triggers:**
- Push of version tags (e.g., `v1.2.3`)

**What it does:**
- Runs tests (unless hotfix tag)
- Builds and pushes Docker image to GitHub Container Registry
- Creates version badge
- Tags image with semantic versions

**Execution time:**
- Regular release: ~4 minutes (with tests)
- Hotfix release: ~30 seconds (skips tests)

**Key features:**
- Hotfix support (see below)
- Multi-tag strategy (version, major.minor, major, latest)
- Version badge generation
- Higher coverage requirement (83% vs 80%)

## Release Strategies

### Regular Release (with tests)

Use for normal releases where you want full test validation:

```bash
git tag v1.2.3
git push origin v1.2.3
```

**Process:**
1. Runs full test suite (~4 minutes)
2. Builds Docker image
3. Pushes to GHCR
4. Updates version badge

**Total time:** ~4 minutes

### Hotfix Release (skip tests)

Use for emergency production fixes where speed is critical:

```bash
git tag v1.2.3-hotfix
git push origin v1.2.3-hotfix
```

**Process:**
1. ⚠️ **Skips tests** (tests job is skipped)
2. Builds Docker image immediately
3. Pushes to GHCR
4. Updates version badge

**Total time:** ~30 seconds

**⚠️ Warning:** Hotfix releases bypass all testing. Use only for critical production issues where:
- The fix is small and well-understood
- Manual testing has been performed
- Waiting 4 minutes for CI tests would cause significant impact

## Docker Image Tags

When you push `v1.2.3`, the following tags are created:

- `ghcr.io/owner/repo:1.2.3` (full version)
- `ghcr.io/owner/repo:1.2` (major.minor)
- `ghcr.io/owner/repo:1` (major)
- `ghcr.io/owner/repo:latest` (latest release)

## Badges

Two badges are automatically maintained in the `badges` branch:

### Coverage Badge
- Updated on every push to `main` (after tests pass)
- Shows current test coverage percentage
- URL: `https://raw.githubusercontent.com/owner/repo/badges/coverage.svg`

### Version Badge
- Updated on every release tag
- Shows current version number
- URL: `https://raw.githubusercontent.com/owner/repo/badges/version.svg`

## Environment Variables

All workflows require these environment variables (set automatically in CI):

```yaml
DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
DJANGO_SETTINGS_MODULE: config.settings
SECRET_KEY: test-secret-key-for-ci-${{ github.run_id }}
DEBUG: "False"
ENVIRONMENT: development
EXTERNAL_PASS: "test-external-pass"
LIBRARY_API_URL: "https://library-test.example.com/api"
LIBRARY_BEARER_TOKEN: "test-bearer-token"
IT_ASSETS_ACCESS_TOKEN: "test-it-assets-token"
IT_ASSETS_USER: "test-user"
PRINCE_SERVER_URL: ""
DEFAULT_FROM_EMAIL: "test-noreply@example.com"
SPMS_MAINTAINER_EMAIL: "test-maintainer@example.com"
EMAIL_HOST: "localhost"
EMAIL_PORT: "25"
```

## Performance Optimization

### Parallel Testing

Tests run in parallel using pytest-xdist:

```bash
poetry run pytest -n auto
```

**Local (16 cores):** ~6 seconds
**CI (4 cores):** ~4 minutes

The `-n auto` flag automatically detects available CPU cores and distributes tests across them.

### Caching

Both Poetry dependencies and Docker layers are cached:

- **Poetry cache:** Speeds up dependency installation
- **Docker cache:** Speeds up image builds (layer reuse)

## Troubleshooting

### Tests failing in CI but passing locally

Check environment variables - CI uses test values that may differ from your local `.env`.

### Hotfix release still running tests

Ensure tag contains "hotfix" (case-sensitive):
- ✅ `v1.2.3-hotfix`
- ✅ `v1.2.3-hotfix.1`
- ❌ `v1.2.3-HOTFIX` (wrong case)
- ❌ `v1.2.3-fix` (missing "hotfix")

### Badge not updating

Badges are stored in the `badges` branch. Check:
1. Branch exists: `git ls-remote --heads origin badges`
2. Workflow has write permissions
3. Badge generation step succeeded (check workflow logs)

### Docker image not found

Images are only pushed on release tags (not on regular commits). Check:
1. Tag was pushed: `git tag -l`
2. Release workflow completed successfully
3. You're using the correct registry URL: `ghcr.io/owner/repo`

## Quick Reference

| Action | Command | Time | Tests |
|--------|---------|------|-------|
| Run tests locally | `poetry run pytest -n auto` | ~6s | ✅ |
| Push to main | `git push origin main` | ~4min | ✅ |
| Regular release | `git tag v1.2.3 && git push origin v1.2.3` | ~4min | ✅ |
| Hotfix release | `git tag v1.2.3-hotfix && git push origin v1.2.3-hotfix` | ~30s | ❌ |
