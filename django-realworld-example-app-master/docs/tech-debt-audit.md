# Tech Debt Audit — Quality Strategy & Metrics

> **Date:** 2026-02-18
> **Project:** Conduit Django RealWorld Example App
> **Methodology:** Static complexity analysis (line count, class/method count, code smells, SOLID violations, duplication, security risks)

## Table of Contents

1. [Methodology](#methodology)
2. [Hotspot #1 — articles/views.py](#hotspot-1--articlesviewspy)
3. [Hotspot #2 — authentication/models.py](#hotspot-2--authenticationmodelspy)
4. [Hotspot #3 — authentication/serializers.py](#hotspot-3--authenticationserializerspy)
5. [Priority Matrix](#priority-matrix)
6. [Quality Gates](#quality-gates)
7. [SonarQube Configuration](#sonarqube-configuration)

---

## Methodology

Since the repository has only 7 commits (the entire Django source was added in a single commit), traditional git churn analysis is not meaningful. Instead, hotspots were identified through **static complexity analysis** examining:

- **Line count and structural complexity** — number of classes, methods, and nesting depth per file.
- **Code smells** — duplicated logic, dead code, interface inconsistencies.
- **SOLID violations** — Single Responsibility Principle (SRP), Open/Closed Principle (OCP), and Dependency Inversion Principle (DIP) breaches.
- **Security risks** — missing authorization checks, data consistency gaps.
- **Portability and compatibility bugs** — platform-dependent code, library version incompatibilities.

The **Strangler Fig Pattern** was chosen as the refactoring strategy for all three hotspots. This pattern — originally described by Martin Fowler — allows incremental replacement of legacy code by building new implementations alongside old ones, routing traffic to the new code one endpoint at a time, and retiring the old code only after the migration is complete. This approach minimizes risk because:

1. The old code remains functional throughout the migration (zero downtime).
2. Each migration step is independently testable and reversible.
3. It avoids the "big bang rewrite" anti-pattern, which historically has a high failure rate.

---

## Hotspot #1 — `conduit/apps/articles/views.py`

**232 lines | 6 classes | 12+ methods**
**Risk: HIGH | Impact: HIGH**

### Issues Identified

| # | Issue | Category | Lines Affected |
|---|-------|----------|----------------|
| 1 | 4 duplicated `try/except Article.DoesNotExist` blocks with near-identical error messages | **DRY violation** | L74-77, L90-93, L132-135, L169-172, L184-187 |
| 2 | `ArticlesFavoriteAPIView.post` and `.delete` are near-identical (only differ in `favorite`/`unfavorite` call and status code) | **DRY violation** | L165-193 |
| 3 | `ArticleViewSet.update` performs no ownership check — any authenticated user can edit any article | **Security flaw (Broken Access Control — OWASP A01)** | L87-106 |
| 4 | `CommentsDestroyAPIView.destroy` performs no ownership check — any authenticated user can delete any comment | **Security flaw (Broken Access Control — OWASP A01)** | L149-157 |
| 5 | `queryset` class attribute on `ArticleViewSet` (L20) is overridden in every method via `self.queryset.get()` — dead declaration that misleads readers | **Dead code** | L20 |
| 6 | 6 fragmented view classes with no shared base class or mixin for common patterns (slug lookup, serializer context building) | **Missing abstraction** | Entire file |
| 7 | `ArticleViewSet` uses `CreateModelMixin`, `ListModelMixin`, `RetrieveModelMixin` but adds `update` as a plain method — inconsistent interface contract | **Interface inconsistency (LSP concern)** | L14-17 vs L87 |

### Engineering Analysis

**Why this is the highest-priority hotspot:**

The security flaws (issues #3 and #4) represent **Broken Access Control**, which is the #1 risk in the OWASP Top 10 (2021). Any authenticated user can modify or delete content they do not own. In a production environment, this would be a critical vulnerability.

Beyond security, the five duplicated `try/except` blocks violate the **DRY (Don't Repeat Yourself) principle**. Each block follows the same pattern:

```python
try:
    article = Article.objects.get(slug=slug)
except Article.DoesNotExist:
    raise NotFound('An article with this slug does not exist.')
```

This duplication increases the maintenance burden: if the error message format changes, or if we need to add logging on lookup failures, we must update 5 locations.

The `ArticlesFavoriteAPIView` further violates DRY — its `post` and `delete` methods (L165-193) share ~80% of their code. The only differences are:
- `profile.favorite(article)` vs `profile.unfavorite(article)`
- `HTTP_201_CREATED` vs `HTTP_200_OK`

### Strangler Fig Refactoring Plan

**Phase 1 — Create parallel module (Low risk)**
1. Create `conduit/apps/articles/views_v2.py` alongside the existing `views.py`.
2. Extract a `get_article_by_slug(slug)` helper function to eliminate the duplicated `try/except` blocks. This follows the **Extract Method** refactoring pattern:

```python
# views_v2.py
from rest_framework.exceptions import NotFound
from .models import Article

def get_article_by_slug(slug):
    """Centralized article lookup — eliminates 5 duplicated try/except blocks."""
    try:
        return Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        raise NotFound('An article with this slug does not exist.')
```

**Phase 2 — Add authorization (High impact, addresses security flaw)**
3. Create an `IsAuthorOrReadOnly` permission class in `conduit/apps/articles/permissions.py`. This applies the **Strategy Pattern** — DRF's permission system lets us swap authorization strategies declaratively:

```python
# permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    """Allow write operations only if the request user is the author."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user.profile
```

4. Apply `IsAuthorOrReadOnly` to `ArticleViewSet` (for `update`) and `CommentsDestroyAPIView` (for `destroy`).

**Phase 3 — Consolidate favorites (Medium impact)**
5. Refactor `ArticlesFavoriteAPIView` by extracting a `_toggle_favorite` helper:

```python
def _toggle_favorite(self, request, article_slug, action, success_status):
    profile = request.user.profile
    article = get_article_by_slug(article_slug)
    getattr(profile, action)(article)
    serializer = self.serializer_class(article, context={'request': request})
    return Response(serializer.data, status=success_status)
```

**Phase 4 — Route migration (Incremental)**
6. Update `conduit/apps/articles/urls.py` to route endpoints to `views_v2.py` one at a time. Start with the security-critical endpoints (`update`, `destroy`).
7. Keep `views.py` alive as a fallback until all routes are migrated.

**Phase 5 — Cleanup**
8. Delete `views.py` once all routes point to `views_v2.py`.
9. Rename `views_v2.py` to `views.py`.

---

## Hotspot #2 — `conduit/apps/authentication/models.py`

**139 lines | 2 classes | 8 methods**
**Risk: MEDIUM-HIGH | Impact: HIGH**

### Issues Identified

| # | Issue | Category | Lines Affected |
|---|-------|----------|----------------|
| 1 | JWT generation logic (`_generate_jwt_token`) lives inside the `User` model | **SRP violation** | L127-139 |
| 2 | `int(dt.strftime('%s'))` — the `%s` format specifier is not part of the C standard and **does not work on Windows** | **Latent bug (portability)** | L136 |
| 3 | `token.decode('utf-8')` — PyJWT >= 2.0 returns `str` instead of `bytes`, causing `AttributeError` | **Compatibility bug** | L139 |
| 4 | The `token` property re-generates the JWT on every access — no caching | **Performance smell** | L100-109 |
| 5 | In `conduit/apps/authentication/signals.py`, the `is` operator is used for integer comparison (`instance.pk is None` after `.save()` may not behave as expected for non-cached integers) | **Correctness concern** | signals.py |

### Engineering Analysis

**SRP Violation (Single Responsibility Principle):**
The `User` model has two responsibilities: (1) representing user identity and managing authentication state, and (2) generating JWT tokens. According to SRP, a class should have only one reason to change. Currently, the `User` model must change if either the user schema changes *or* the token generation strategy changes (e.g., switching from HS256 to RS256, adding claims, changing expiry).

**Portability Bug:**
The `strftime('%s')` call (L136) relies on a platform-specific extension. On Windows, this raises `ValueError` because `%s` is not a recognized directive. The portable alternative is `datetime.timestamp()` (Python 3.3+) or `calendar.timegm()`.

**PyJWT Compatibility:**
Starting with PyJWT 2.0 (released January 2021), `jwt.encode()` returns a `str` instead of `bytes`. Calling `.decode('utf-8')` on a `str` raises `AttributeError: 'str' object has no attribute 'decode'`. This is a breaking change that would surface immediately upon upgrading PyJWT.

### Strangler Fig Refactoring Plan

**Phase 1 — Create TokenService (Low risk)**
1. Create `conduit/apps/authentication/services.py` with a `TokenService` class. This applies the **Extract Class** refactoring and follows the **Service Layer Pattern** — domain logic (JWT generation) moves out of the data model into a dedicated service:

```python
# services.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings

class TokenService:
    """Encapsulates JWT token generation — extracted from User model (SRP)."""

    TOKEN_EXPIRY_DAYS = 60
    ALGORITHM = 'HS256'

    @classmethod
    def generate_token(cls, user):
        dt = datetime.now() + timedelta(days=cls.TOKEN_EXPIRY_DAYS)

        payload = {
            'id': user.pk,
            'exp': int(dt.timestamp())  # Portable — works on all platforms
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=cls.ALGORITHM)

        # PyJWT >= 2.0 returns str; PyJWT < 2.0 returns bytes
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
```

**Phase 2 — Bridge via delegation (Zero breakage)**
2. Update `User.token` property to delegate to `TokenService`:

```python
@property
def token(self):
    from .services import TokenService
    return TokenService.generate_token(self)
```

This is the "strangler bridge" — external callers still access `user.token` and see no difference, but the implementation now lives in `TokenService`.

**Phase 3 — Migrate callers (Incremental)**
3. Update serializers (`RegistrationSerializer`, `LoginSerializer`, `UserSerializer`) to call `TokenService.generate_token(user)` directly instead of `user.token`.

**Phase 4 — Cleanup**
4. Once all callers use `TokenService`, remove the `token` property and `_generate_jwt_token` method from the `User` model.

---

## Hotspot #3 — `conduit/apps/authentication/serializers.py`

**177 lines | 3 classes | 4 methods**
**Risk: MEDIUM | Impact: MEDIUM-HIGH**

### Issues Identified

| # | Issue | Category | Lines Affected |
|---|-------|----------|----------------|
| 1 | `LoginSerializer.validate` performs authentication + authorization + response shaping in a single method | **SRP violation** | L42-96 |
| 2 | `UserSerializer.update` calls `instance.save()` (L166) and `instance.profile.save()` (L174) without `@transaction.atomic` — if the profile save fails, user data is partially committed | **Data consistency risk** | L139-176 |
| 3 | `from conduit.apps.profiles.serializers import ProfileSerializer` — cross-app import creates tight coupling between `authentication` and `profiles` | **Coupling smell (DIP violation)** | L5 |
| 4 | `profile` field is declared `write_only=True` (L115) while `bio` and `image` are `read_only=True` (L119-120) — bidirectional read/write representation of the same data through different field paths | **Confusing API design** | L115-120 |

### Engineering Analysis

**SRP Violation in `LoginSerializer.validate`:**
This 55-line method (L42-96) handles three distinct responsibilities:
1. **Input validation** — checking that email and password are present.
2. **Authentication** — calling `django.contrib.auth.authenticate()`.
3. **Response construction** — building the return dictionary with email, username, and token.

According to SRP, each of these should be a separate concern. The validate method should only validate input; authentication should be delegated to a service; and response shaping is the serializer's `to_representation` concern.

**Data Consistency Risk:**
In `UserSerializer.update` (L139-176), the user is saved first (L166), then the profile is saved (L174). If the profile save raises an exception (e.g., database constraint violation), the user changes are already committed. This violates the **Atomicity** property — either both saves should succeed or neither should. The fix is straightforward: wrap the method in `@transaction.atomic`.

**Cross-App Coupling:**
The import of `ProfileSerializer` from `conduit.apps.profiles` (L5) creates a direct dependency from the `authentication` app to the `profiles` app. This violates the **Dependency Inversion Principle (DIP)** — high-level modules (authentication) should not depend on low-level modules (profiles). In a well-layered Django project, apps should communicate through well-defined interfaces or Django signals, not direct imports of each other's serializers.

### Strangler Fig Refactoring Plan

**Phase 1 — Create AuthenticationService (Low risk)**
1. Add an `authenticate(email, password)` method to `services.py` (created in Hotspot #2):

```python
# In services.py
from django.contrib.auth import authenticate as django_authenticate

class AuthenticationService:
    """Encapsulates authentication logic — extracted from LoginSerializer (SRP)."""

    @staticmethod
    def authenticate(email, password):
        if not email:
            raise ValueError('An email address is required to log in.')
        if not password:
            raise ValueError('A password is required to log in.')

        user = django_authenticate(username=email, password=password)

        if user is None:
            raise ValueError('A user with this email and password was not found.')
        if not user.is_active:
            raise ValueError('This user has been deactivated.')

        return user
```

**Phase 2 — Create v2 serializers (Low risk)**
2. Create `conduit/apps/authentication/serializers_v2.py`.
3. Implement `LoginSerializerV2.validate` — it only validates input format, then delegates to `AuthenticationService.authenticate()`:

```python
class LoginSerializerV2(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        user = AuthenticationService.authenticate(
            data.get('email'), data.get('password')
        )
        return {
            'email': user.email,
            'username': user.username,
            'token': TokenService.generate_token(user)
        }
```

4. Implement `UserSerializerV2.update` wrapped in `@transaction.atomic`:

```python
from django.db import transaction

class UserSerializerV2(serializers.ModelSerializer):
    # ... same field declarations ...

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        profile_data = validated_data.pop('profile', {})

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if password is not None:
            instance.set_password(password)

        instance.save()

        for key, value in profile_data.items():
            setattr(instance.profile, key, value)

        instance.profile.save()
        return instance
```

**Phase 3 — Route migration (Incremental)**
5. Update `LoginAPIView` to use `LoginSerializerV2` and `UserRetrieveUpdateAPIView` to use `UserSerializerV2`.

**Phase 4 — Cleanup**
6. Remove old serializer classes once all views use v2 serializers.
7. Rename `serializers_v2.py` to `serializers.py`.

---

## Priority Matrix

The hotspots are prioritized using a **Risk × Impact** matrix, where:
- **Risk** measures the severity of existing issues (security flaws > compatibility bugs > code smells).
- **Impact** measures how many features/endpoints are affected and the blast radius of a failure.

| Priority | Hotspot | Risk | Impact | Rationale |
|----------|---------|------|--------|-----------|
| **P0 — Critical** | `articles/views.py` | HIGH | HIGH | Contains active **security vulnerabilities** (missing ownership checks on update and delete). Highest structural complexity (6 classes, 12+ methods). Most code duplication (5 repeated `try/except` blocks). Affects the most API endpoints (8 of 14 total endpoints). |
| **P1 — High** | `authentication/models.py` | MEDIUM-HIGH | HIGH | Contains **compatibility bugs** that break on Windows (`strftime('%s')`) and on PyJWT >= 2.0 (`.decode('utf-8')`). SRP violation at the core `User` model means every token-related change requires modifying the model. High impact because JWT generation affects all authenticated requests. |
| **P2 — Medium** | `authentication/serializers.py` | MEDIUM | MEDIUM-HIGH | **Data consistency risk** (non-atomic dual save) and SRP violations. Lower blast radius than P0/P1 because failures are isolated to login and user-update endpoints. Cross-app coupling is a maintainability concern but not an immediate runtime risk. |

### Recommended Execution Order

```
Week 1: P0 — Fix security flaws in articles/views.py
         - Create IsAuthorOrReadOnly permission (immediate security fix)
         - Extract get_article_by_slug helper

Week 2: P1 — Extract TokenService from User model
         - Fix strftime('%s') portability bug
         - Handle PyJWT 2.x compatibility

Week 3: P2 — Refactor authentication serializers
         - Add @transaction.atomic to UserSerializer.update
         - Extract AuthenticationService
```

---

## Quality Gates

Quality gates define the **minimum quality criteria** that new code must meet before it can be merged into the main branch. These gates are enforced via SonarQube as part of the CI/CD pipeline.

### Gate Definitions

| Gate | Metric | Threshold | Rationale |
|------|--------|-----------|-----------|
| **Reliability** | New bugs on changed code | **0** | No new bugs may be introduced on any PR. This is the strictest possible threshold — zero tolerance for regression. |
| **Security** | New vulnerabilities on changed code | **0** | No new security issues allowed. This directly addresses the Broken Access Control findings in Hotspot #1. |
| **Maintainability** | Technical debt ratio on new code | **≤ 5%** | Allows the team to focus on strangling legacy debt without being blocked by it, while ensuring all *new* code is clean. The 5% threshold means that for every 100 lines of new code, at most 5 lines may carry unresolved code smells. |
| **Duplication** | Duplicated lines on new code | **≤ 3%** | Enforces DRY on new contributions. This threshold is stricter than the SonarQube default (which is often not set) because duplication is the single most prevalent issue found in this audit. |
| **Coverage** | Line coverage on new code | **≥ 80%** | Since the project currently has **zero test coverage**, this gate ensures that all new code is tested. The 80% threshold is an industry standard that balances thoroughness with practicality (some lines like exception handlers may be hard to cover). |
| **Complexity** | Cognitive complexity per method | **≤ 15** | Prevents the formation of new hotspots. SonarQube's cognitive complexity metric measures how hard a method is to understand (considering nesting, breaks in linear flow, and recursion). A threshold of 15 is the SonarQube default recommendation. |

### How Quality Gates Interact with the Strangler Fig Strategy

The quality gates are configured to evaluate **new code only** (not the entire codebase). This is critical because:

1. The legacy code (which we are strangling) would fail multiple gates (e.g., `LoginSerializer.validate` has cognitive complexity > 15, there is 0% test coverage).
2. By scoping gates to new code, the team can merge Strangler Fig refactorings incrementally without the legacy code blocking the pipeline.
3. As legacy code is replaced, the overall codebase metrics improve organically.

### Enforcement Mechanism

Quality gates are enforced at two levels:

1. **SonarQube Server** — The quality gate is configured in the SonarQube UI under *Quality Gates > Create*. The gate is applied to the project `conduit-realworld-django`.
2. **CI Pipeline** — The `sonar-scanner` is invoked as a step in the CI pipeline (e.g., GitHub Actions). If the quality gate fails, the pipeline fails and the PR cannot be merged.

---

## SonarQube Configuration

The project is configured via `sonar-project.properties` at the repository root. Key configuration decisions:

| Property | Value | Rationale |
|----------|-------|-----------|
| `sonar.projectKey` | `conduit-realworld-django` | Unique identifier for the project in SonarQube. |
| `sonar.sources` | `conduit` | All application code lives under the `conduit/` directory. |
| `sonar.language` | `py` | The project is a Python (Django) application. |
| `sonar.exclusions` | `**/migrations/**,**/tests/**,manage.py` | Django migrations are auto-generated and should not be analyzed. Test files have different quality standards. `manage.py` is boilerplate. |

### SonarQube Setup Steps

1. **Install SonarQube** (Community Edition is free and sufficient for this project).
2. **Create the project** in the SonarQube UI with key `conduit-realworld-django`.
3. **Configure the quality gate** using the thresholds defined above.
4. **Generate an authentication token** for the CI pipeline.
5. **Add `sonar-project.properties`** to the repository root (already done — see file in repo root).
6. **Integrate with CI** — add a `sonar-scanner` step to the GitHub Actions workflow (separate deliverable).

---

## Appendix: Design Patterns Referenced

| Pattern | Where Applied | Description |
|---------|---------------|-------------|
| **Strangler Fig** | All hotspots | Incremental replacement of legacy code by building new implementations alongside old ones, migrating traffic, and retiring the old code. Avoids big-bang rewrites. |
| **Strategy Pattern** | `IsAuthorOrReadOnly` permission | DRF's permission system uses the Strategy pattern — permission classes are interchangeable strategies for authorization decisions. |
| **Service Layer Pattern** | `TokenService`, `AuthenticationService` | Extracts domain logic from models and serializers into dedicated service classes, following SRP. |
| **Extract Method** | `get_article_by_slug()` | Consolidates duplicated code into a single, reusable method. |
| **Extract Class** | `TokenService` from `User` | Moves a cohesive set of responsibilities from one class to a new, dedicated class. |

## Appendix: SOLID Principles Referenced

| Principle | Violations Found | Hotspot |
|-----------|-----------------|---------|
| **SRP** (Single Responsibility) | JWT generation in User model; auth + validation + response in LoginSerializer.validate | #2, #3 |
| **OCP** (Open/Closed) | Adding new article actions requires modifying existing view classes | #1 |
| **LSP** (Liskov Substitution) | ArticleViewSet declares mixins but adds `update` method outside the mixin contract | #1 |
| **DIP** (Dependency Inversion) | Direct cross-app import of ProfileSerializer in authentication serializers | #3 |
