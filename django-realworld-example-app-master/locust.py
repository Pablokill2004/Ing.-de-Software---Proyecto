"""Locust benchmark for Conduit (Django RealWorld API).

Goal
----
Keep the load test easy to read and explain while still stressing the
typical "hot paths" that are affected by N+1 and ORM inefficiencies.

This script focuses on core endpoints:
- Articles: list + filters + detail
- Tags: list
- Profiles: profile detail

Auth is optional:
- If you provide `CONDUIT_EMAIL` + `CONDUIT_PASSWORD`, Locust will login once
  per simulated user and reuse the JWT.
- If you do not provide credentials, all tasks still work (they are public).

Run examples (PowerShell)
-------------------------
From the repo root:

  uvx locust -f "django-realworld-example-app-master\locust.py" \
    --host "http://localhost:8000"

Headless quick validation:

  uvx locust -f "django-realworld-example-app-master\locust.py" \
    --host "http://localhost:8000" --headless -u 20 -r 5 -t 1m --only-summary

Optional knobs (env vars)
-------------------------
- `CONDUIT_API_PREFIX` (default: /api)
- `LOCUST_WAIT_MIN` / `LOCUST_WAIT_MAX` (seconds)
- `LOCUST_ARTICLES_LIMIT` (default: 20)
- `CONDUIT_EMAIL` / `CONDUIT_PASSWORD` (enables login + authenticated headers)
"""

from __future__ import annotations

import os
import random
from typing import Dict, List, Optional

from locust import HttpUser, between, task
from locust.exception import StopUser


def env_int(name: str, default: int) -> int:
    """Read an integer env var with a safe default."""

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class ConduitUser(HttpUser):
    """A single simulated user hitting the Conduit API."""

    # Time between tasks (think-time). Keep it small but non-zero.
    wait_time = between(
        float(os.getenv("LOCUST_WAIT_MIN", "0.2")),
        float(os.getenv("LOCUST_WAIT_MAX", "1.2")),
    )

    # API settings
    api_prefix = os.getenv("CONDUIT_API_PREFIX", "/api")

    # (Optional) default host to reduce UI mistakes.
    # You can still override it in the UI host field or via `--host`.
    host = os.getenv("LOCUST_HOST", "")

    # Per-user caches so we can do realistic follow-up calls.
    _slugs: List[str]
    _tags: List[str]
    _usernames: List[str]

    # Optional JWT token (only if login is configured).
    _token: Optional[str]

    # -----------------
    # Lifecycle
    # -----------------

    def on_start(self) -> None:
        """Initialize caches and (optionally) login."""

        # Guardrails: avoid typos like 'htttp://' that produce only exceptions.
        host = (self.host or "").strip()
        if host and not (host.startswith("http://") or host.startswith("https://")):
            raise StopUser(
                f"Invalid host scheme: {host!r}. Use 'http://' or 'https://'."
            )

        self._slugs = []
        self._tags = []
        self._usernames = []
        self._token = None

        email = os.getenv("CONDUIT_EMAIL")
        password = os.getenv("CONDUIT_PASSWORD")
        if email and password:
            self._token = self._login(email=email, password=password)

        # Seed tags early so filtered article listing can run immediately.
        self._seed_tags()

    # -----------------
    # Small helpers
    # -----------------

    def _auth_headers(self) -> Dict[str, str]:
        """Return auth headers if we have a JWT token."""

        if not self._token:
            return {}
        # Conduit expects: Authorization: Token <jwt>
        return {"Authorization": f"Token {self._token}"}

    def _login(self, email: str, password: str) -> Optional[str]:
        """Login and extract JWT from response.

        RealWorld contract:
          POST /api/users/login
          {"user": {"email": "...", "password": "..."}}
        returns:
          {"user": {"email": "...", "username": "...", "token": "..."}}
        """

        payload = {"user": {"email": email, "password": password}}

        with self.client.post(
            f"{self.api_prefix}/users/login",
            json=payload,
            name="POST /api/users/login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"login failed: {resp.status_code} {resp.text[:200]}")
                return None

            try:
                data = resp.json()
            except Exception:
                resp.failure("login: non-JSON response")
                return None

            token = (data.get("user") or {}).get("token")
            if not token:
                resp.failure("login: missing token")
                return None

            resp.success()
            return token

    def _pick_slug(self) -> Optional[str]:
        """Pick a known article slug; seed cache if needed."""

        if self._slugs:
            return random.choice(self._slugs)

        # Seed with a small list request.
        with self.client.get(
            f"{self.api_prefix}/articles?limit=5&offset=0",
            name="GET /api/articles (seed)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"seed failed: {resp.status_code}")
                return None

            try:
                data = resp.json()
            except Exception:
                resp.failure("seed: non-JSON response")
                return None

            articles = data.get("articles") or []
            slugs = [a.get("slug") for a in articles if a.get("slug")]
            if not slugs:
                resp.success()
                return None

            self._slugs.extend(slugs)
            self._slugs = self._slugs[-50:]
            resp.success()
            return random.choice(slugs)

    def _seed_tags(self) -> None:
        """Fetch tags once to enable tag-filtered listing early."""

        try:
            resp = self.client.get(
                f"{self.api_prefix}/tags",
                name="GET /api/tags (seed)",
            )
        except Exception:
            return

        if resp.status_code != 200:
            return

        try:
            data = resp.json()
        except Exception:
            return

        tags = data.get("tags")
        if isinstance(tags, list) and tags:
            self._tags = [t for t in tags if isinstance(t, str)][:50]

    def _pick_username(self) -> Optional[str]:
        """Pick a known username for /profiles calls."""

        if self._usernames:
            return random.choice(self._usernames)
        return None

    # -----------------
    # Core benchmark tasks
    # -----------------

    @task(10)
    def articles_list(self) -> None:
        """Hot path: list articles (pagination).

        This is commonly where N+1 shows up because list rendering touches:
        - author profile
        - tags (many-to-many)
        - favorites count
        """

        limit = env_int("LOCUST_ARTICLES_LIMIT", 20)
        offset = random.randint(0, 200)

        with self.client.get(
            f"{self.api_prefix}/articles?limit={limit}&offset={offset}",
            name="GET /api/articles (list)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"articles_list failed: {resp.status_code}")
                return

            try:
                data = resp.json()
            except Exception:
                resp.failure("articles_list: non-JSON response")
                return

            articles = data.get("articles")
            if isinstance(articles, list) and articles:
                # Cache some slugs and authors for follow-up calls.
                sample = random.sample(articles, k=min(5, len(articles)))
                for article in sample:
                    slug = article.get("slug")
                    if slug:
                        self._slugs.append(slug)

                    author = (article.get("author") or {}).get("username")
                    if author:
                        self._usernames.append(author)

                # Keep caches bounded.
                self._slugs = self._slugs[-50:]
                self._usernames = self._usernames[-50:]

            resp.success()

    @task(3)
    def articles_list_filtered(self) -> None:
        """List articles with a filter (tag or author).

        Filters are useful to surface ORM issues around joins/prefetching.
        """

        limit = env_int("LOCUST_ARTICLES_LIMIT", 20)

        # Prefer tag filter (many-to-many) if we have any tags cached.
        if self._tags:
            tag = random.choice(self._tags)
            self.client.get(
                f"{self.api_prefix}/articles?tag={tag}&limit={limit}&offset=0",
                name="GET /api/articles?tag= (list)",
            )
            return

        # Fallback to author filter.
        username = self._pick_username()
        if username:
            self.client.get(
                f"{self.api_prefix}/articles?author={username}&limit={limit}&offset=0",
                name="GET /api/articles?author= (list)",
            )

    @task(3)
    def article_detail(self) -> None:
        """Get a single article by slug."""

        slug = self._pick_slug()
        if not slug:
            return
        self.client.get(
            f"{self.api_prefix}/articles/{slug}",
            name="GET /api/articles/:slug (detail)",
        )

    @task(2)
    def profile_detail(self) -> None:
        """Get a profile by username."""

        username = self._pick_username()
        if not username:
            return
        self.client.get(
            f"{self.api_prefix}/profiles/{username}",
            name="GET /api/profiles/:username",
            headers=self._auth_headers(),
        )

    @task(1)
    def tags_list(self) -> None:
        """Fetch tags and keep a small cache for filtered list calls."""

        with self.client.get(
            f"{self.api_prefix}/tags",
            name="GET /api/tags",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"tags_list failed: {resp.status_code}")
                return

            try:
                data = resp.json()
            except Exception:
                resp.failure("tags_list: non-JSON response")
                return

            tags = data.get("tags")
            if isinstance(tags, list) and tags:
                # Keep only a few tags; enough to drive filters.
                self._tags = [t for t in tags if isinstance(t, str)][:50]

            resp.success()
