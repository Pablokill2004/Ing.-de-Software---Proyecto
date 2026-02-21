# Changelog — Architectural Decisions & Refactorings

This file tracks significant architectural changes, refactorings, and design decisions made to the codebase. It serves as future context so that anyone (human or AI) working on the project understands what was done, why, and what patterns are now in place.

---

## 2026-02-18 — Tech Debt Audit & Strangler Fig Refactoring

**Audit document:** `docs/tech-debt-audit.md`
**Branch:** `sosa`

A static complexity analysis identified the top 3 tech debt hotspots. All three were refactored using the Strangler Fig pattern — new code was built alongside old code, then the old code was replaced.

### P0: `conduit/apps/articles/views.py` — Security + DRY

**Commits:** `4942df9`

**What changed:**
- Created `conduit/apps/articles/permissions.py` with `IsAuthorOrReadOnly` permission class.
- `ArticleViewSet.update` now calls `check_object_permissions()` — only the article author can update.
- `CommentsDestroyAPIView.destroy` now calls `check_object_permissions()` — only the comment author can delete.
- Extracted `get_article_by_slug(slug)` helper function, replacing 5 duplicated `try/except Article.DoesNotExist` blocks.
- Consolidated `ArticlesFavoriteAPIView.post`/`delete` into a shared `_toggle_favorite()` helper.

**Why:**
- The missing ownership checks were OWASP A01 (Broken Access Control) vulnerabilities — any authenticated user could edit any article or delete any comment.
- The 5 duplicated try/except blocks violated DRY and made error message changes require 5 edits.

**Patterns:** Strategy Pattern (permission class), Extract Method (slug helper).

---

### P1: `conduit/apps/authentication/models.py` — SRP + Bug Fixes

**Commits:** `5697a3c`

**What changed:**
- Created `conduit/apps/authentication/services.py` with:
  - `TokenService.generate_token(user)` — JWT generation extracted from User model.
  - `AuthenticationService.authenticate(email, password)` — login logic extracted from LoginSerializer.
- `User.token` property now delegates to `TokenService.generate_token(self)` (Strangler Fig bridge).
- Fixed `int(dt.strftime('%s'))` → `int(dt.timestamp())` — the `%s` format doesn't work on Windows.
- Fixed PyJWT 2.x compatibility — `jwt.encode()` returns `str` in 2.x, not `bytes`.
- Removed unused imports (`jwt`, `datetime`, `timedelta`, `settings`) from `models.py`.

**Why:**
- The User model had two reasons to change (user schema + token strategy) — SRP violation.
- The `strftime('%s')` bug would crash on Windows. The `.decode('utf-8')` bug would crash on PyJWT >= 2.0.

**Patterns:** Service Layer Pattern, Extract Class refactoring.

**Note:** `User.token` still works as a bridge for any callers not yet migrated. Once all callers use `TokenService` directly, the property can be removed.

---

### P2: `conduit/apps/authentication/serializers.py` — SRP + Atomicity

**Commits:** `347f0d6`

**What changed:**
- `LoginSerializer.validate` now delegates to `AuthenticationService.authenticate()` instead of calling `django.contrib.auth.authenticate` directly. Service errors (`ValueError`) are caught and re-raised as `serializers.ValidationError`.
- `LoginSerializer.validate` now calls `TokenService.generate_token(user)` directly instead of `user.token`.
- `UserSerializer.update` is now wrapped in `@transaction.atomic` — if `instance.profile.save()` fails, the `instance.save()` is rolled back.
- Removed unused `from django.contrib.auth import authenticate` import.

**Why:**
- `LoginSerializer.validate` was doing three things (input validation, authentication, response shaping) — SRP violation.
- The dual-save without a transaction meant a profile save failure left user data partially committed.

**Patterns:** Service Layer Pattern. **Principles:** SRP, Atomicity (ACID).

---

### SonarQube Configuration

**Commits:** `5559fa7`

- Added `sonar-project.properties` at repo root.
- Project key: `conduit-realworld-django`, sources: `conduit/`, exclusions: migrations, tests, manage.py.
- Quality gate thresholds documented in comments and in `docs/tech-debt-audit.md`.

---

## Conventions Established

1. **Business logic goes in `services.py`**, not in models or serializers. Models handle data; serializers handle validation/serialization; services handle domain logic.
2. **Object-level permissions** use DRF permission classes (in `permissions.py`), not inline checks in view methods.
3. **Shared lookup helpers** (like `get_article_by_slug`) live at the top of `views.py` as module-level functions.
4. **Commit messages** follow conventional commits (`fix:`, `refactor:`, `docs:`, `ci:`) and explain the pattern/principle that motivated the change.
5. **Quality gates** are scoped to new code only, allowing incremental improvement of legacy code.
