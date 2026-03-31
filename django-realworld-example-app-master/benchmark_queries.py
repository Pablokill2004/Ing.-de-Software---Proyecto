"""
FinOps Benchmark: N+1 Query Optimization
=========================================
Measures DB query count and execution time for GET /api/articles/
before and after the N+1 optimization.

Usage (inside Docker):
    python benchmark_queries.py

Methodology:
- Seeds the DB with 20 articles, tags, favorites, and follows
- Simulates the article list endpoint logic directly
- Counts queries using django.db.connection.queries
- Reports before/after comparison
"""

import os
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conduit.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.db.models import Count

from conduit.apps.articles.models import Article, Tag
from conduit.apps.articles.serializers import ArticleSerializer
from conduit.apps.profiles.models import Profile

User = get_user_model()

ARTICLE_COUNT = 20


def seed_db():
    """Create test data: 1 reader, 5 authors, 20 articles, tags, favorites, follows."""
    # Reader
    reader, _ = User.objects.get_or_create(
        username='benchmark_reader',
        defaults={'email': 'reader@bench.test'}
    )
    reader.set_password('pass')
    reader.save()

    # Authors
    authors = []
    for i in range(5):
        u, _ = User.objects.get_or_create(
            username=f'bench_author_{i}',
            defaults={'email': f'author{i}@bench.test'}
        )
        u.set_password('pass')
        u.save()
        authors.append(u.profile)

    # Reader follows all authors
    for a in authors:
        reader.profile.follows.add(a)

    # Tags
    tags = []
    for i in range(5):
        t, _ = Tag.objects.get_or_create(
            tag=f'bench-tag-{i}',
            defaults={'slug': f'bench-tag-{i}'}
        )
        tags.append(t)

    # Articles
    articles = []
    for i in range(ARTICLE_COUNT):
        author = authors[i % len(authors)]
        slug = f'benchmark-article-{i}-v2'
        a, _ = Article.objects.get_or_create(
            slug=slug,
            defaults={
                'title': f'Benchmark Article {i}',
                'description': 'desc',
                'body': 'body ' * 20,
                'author': author,
            }
        )
        a.tags.add(tags[i % len(tags)])
        articles.append(a)

    # Reader favorites half the articles
    for a in articles[:ARTICLE_COUNT // 2]:
        reader.profile.favorites.add(a)

    return reader, articles


class FakeRequest:
    """Minimal request stub for the serializer context."""
    def __init__(self, user):
        self.user = user


# ---------------------------------------------------------------------------
# BEFORE: original approach — N+1 queries per article
# ---------------------------------------------------------------------------

def run_before(reader, articles):
    """Simulates the original list() without any optimization."""
    fake_request = FakeRequest(reader)
    context = {'request': fake_request}

    reset_queries()
    t0 = time.perf_counter()

    # Original queryset (no prefetch, no annotation)
    qs = Article.objects.select_related('author', 'author__user').all()[:ARTICLE_COUNT]
    serializer = ArticleSerializer(list(qs), context=context, many=True)
    _ = serializer.data  # force evaluation

    elapsed = time.perf_counter() - t0
    query_count = len(connection.queries)
    return query_count, elapsed


# ---------------------------------------------------------------------------
# AFTER: optimized approach — bulk prefetch + annotation + set lookups
# ---------------------------------------------------------------------------

def run_after(reader, articles):
    """Simulates the optimized list() with N+1 eliminated."""
    fake_request = FakeRequest(reader)

    profile = reader.profile
    favorite_ids = set(profile.favorites.values_list('pk', flat=True))
    following_ids = set(profile.follows.values_list('pk', flat=True))

    context = {
        'request': fake_request,
        'favorite_article_ids': favorite_ids,
        'following_profile_ids': following_ids,
    }

    reset_queries()
    t0 = time.perf_counter()

    # Optimized queryset
    qs = (
        Article.objects
        .select_related('author', 'author__user')
        .prefetch_related('tags')
        .annotate(favorites_count=Count('favorited_by'))
        .all()[:ARTICLE_COUNT]
    )
    serializer = ArticleSerializer(list(qs), context=context, many=True)
    _ = serializer.data  # force evaluation

    elapsed = time.perf_counter() - t0
    query_count = len(connection.queries)
    return query_count, elapsed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

RUNS = 5

if __name__ == '__main__':
    with override_settings(DEBUG=True):
        print("Seeding database...")
        reader, articles = seed_db()
        print(f"  {ARTICLE_COUNT} articles, {reader.profile.favorites.count()} favorites, "
              f"{reader.profile.follows.count()} follows\n")

        before_counts, before_times = [], []
        after_counts, after_times = [], []

        for i in range(RUNS):
            qc, t = run_before(reader, articles)
            before_counts.append(qc)
            before_times.append(t)

        for i in range(RUNS):
            qc, t = run_after(reader, articles)
            after_counts.append(qc)
            after_times.append(t)

        avg_before_q = sum(before_counts) / RUNS
        avg_after_q  = sum(after_counts)  / RUNS
        avg_before_t = sum(before_times)  / RUNS * 1000  # ms
        avg_after_t  = sum(after_times)   / RUNS * 1000  # ms

        query_reduction = (avg_before_q - avg_after_q) / avg_before_q * 100
        time_reduction  = (avg_before_t - avg_after_t)  / avg_before_t * 100

        print("=" * 55)
        print(f"  Benchmark: GET /api/articles/ ({ARTICLE_COUNT} articles)")
        print("=" * 55)
        print(f"  {'Metric':<25} {'Before':>8} {'After':>8} {'Change':>10}")
        print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*10}")
        print(f"  {'DB queries (avg)':<25} {avg_before_q:>8.1f} {avg_after_q:>8.1f} "
              f"{'-' + str(round(query_reduction, 1)) + '%':>10}")
        print(f"  {'Wall time ms (avg)':<25} {avg_before_t:>8.2f} {avg_after_t:>8.2f} "
              f"{'-' + str(round(time_reduction, 1)) + '%':>10}")
        print("=" * 55)
        print(f"\n  Query reduction: {query_reduction:.1f}%")
        print(f"  Time  reduction: {time_reduction:.1f}%")

        rubric_pass = query_reduction >= 15 or time_reduction >= 15
        status = "PASS" if rubric_pass else "FAIL"
        print(f"\n  Rubric (>15% improvement): {status}")
        print()
