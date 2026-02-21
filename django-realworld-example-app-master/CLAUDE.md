# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django RealWorld Example App — a REST API backend implementing the [RealWorld](https://github.com/gothinkster/realworld) spec (Conduit). Built with Django 1.10 + Django REST Framework 3.4 + JWT authentication. No frontend; API-only.

## Educational Context

This repository is used as a **university Software Engineering course project**. All work performed here serves an educational purpose.

- **Technical documentation is required for every task** (features, refactors, bug fixes, etc.). Always explain the engineering rationale, design decisions, patterns applied (name them explicitly — e.g., Repository Pattern, Observer Pattern), and trade-offs considered.
- **Target audience: software engineering students.** Be precise with terminology — cite SOLID principles, name architectural layers (presentation, domain, persistence), and reference relevant design patterns — but also provide enough context so a student encountering the concept for the first time can follow along.
- **Commit messages, PR descriptions, and inline comments** should reflect this standard: explain the *why* behind changes, not just the *what*. For example, a commit message should state which principle or pattern motivated the change, not merely list the files touched.

## Related Context Files

- **`claude/CHANGELOG.md`** — Running log of architectural changes, refactorings, and design decisions. Consult this first to understand recent work and avoid duplicating effort.
- **`docs/tech-debt-audit.md`** — Full tech debt audit with hotspot analysis, Strangler Fig plans, quality gate definitions, and SonarQube setup.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start development server (runs on localhost:8000)
python manage.py runserver

# Create migrations after model changes
python manage.py makemigrations
```

There is no test suite, linter, or Makefile configured in this project.

## Architecture

### Django Apps (under `conduit/apps/`)

- **authentication** — Custom `User` model (`AbstractBaseUser`), JWT token generation/validation, registration & login endpoints. Login is by **email**, not username. A post-save signal auto-creates a `Profile` when a `User` is created.
- **articles** — `Article`, `Comment`, and `Tag` models. Core content domain. Tags are auto-created via `get_or_create` on article creation.
- **profiles** — `Profile` model (1:1 with User). Handles social features: following (self-referential M2M) and favorites (M2M to Article).
- **core** — Shared base classes: `TimestampedModel` (abstract, adds `created_at`/`updated_at`), custom exception handler, base JSON renderer.

### Service Layer (introduced in tech debt refactoring)

- **`authentication/services.py`** — `TokenService` (JWT generation, extracted from User model) and `AuthenticationService` (login logic, extracted from LoginSerializer). All new business logic should go into service classes, not models or serializers.

### Permissions

- **`articles/permissions.py`** — `IsAuthorOrReadOnly` permission class. Enforces object-level ownership checks on write operations. Applied to article update and comment delete endpoints.

### Key Patterns

- **JWT Auth**: Custom `JWTAuthentication` backend in `authentication/backends.py`. Header format: `Authorization: Token <jwt>`. Tokens use HS256 with 60-day expiry. Token generation is handled by `TokenService` (in `services.py`), not the User model.
- **Custom JSON Renderers**: Each app has a renderer (`ConduitJSONRenderer` subclass) that wraps responses in a labeled key (e.g., `{"article": {...}}`).
- **All API routes are under `/api/`** — see `conduit/urls.py` for the full route map.
- **Pagination**: LimitOffsetPagination, default page size 20.
- **Settings**: Single `conduit/settings.py`, SQLite database, `AUTH_USER_MODEL = 'authentication.User'`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/users/` | Register |
| POST | `/api/users/login/` | Login |
| GET/PUT | `/api/user/` | Current user |
| GET | `/api/profiles/{username}/` | View profile |
| POST/DELETE | `/api/profiles/{username}/follow/` | Follow/unfollow |
| GET/POST | `/api/articles/` | List/create articles |
| GET/PUT/DELETE | `/api/articles/{slug}/` | Article detail (update requires author ownership) |
| GET | `/api/articles/feed/` | Feed (followed authors) |
| POST/DELETE | `/api/articles/{slug}/favorite/` | Favorite/unfavorite |
| GET/POST | `/api/articles/{slug}/comments/` | Comments |
| DELETE | `/api/articles/{slug}/comments/{id}/` | Delete comment (requires author ownership) |
| GET | `/api/tags/` | List tags |

### Quality Gates (SonarQube)

Configured in `sonar-project.properties`. Thresholds apply to **new code only**:

| Metric | Threshold |
|--------|-----------|
| New bugs | 0 |
| New vulnerabilities | 0 |
| Tech debt ratio (new code) | ≤ 5% |
| Duplication (new code) | ≤ 3% |
| Line coverage (new code) | ≥ 80% |
| Cognitive complexity per method | ≤ 15 |
