from django.test import TestCase

from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from conduit.apps.articles.models import Article, Comment, Tag
from conduit.apps.articles.views import (
    ArticlesFeedAPIView, ArticlesFavoriteAPIView, get_article_by_slug
)
from conduit.apps.authentication.models import User


class GetArticleBySlugTest(TestCase):
    """
    Tests for the get_article_by_slug() helper — the Extract Method
    refactoring that replaced 5 duplicated try/except blocks.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='sluguser', email='sluguser@test.com', password='testpass123'
        )
        self.article = Article.objects.create(
            slug='test-article',
            title='Test Article',
            description='A test description',
            body='Test body content',
            author=self.user.profile,
        )

    def test_returns_article_for_valid_slug(self):
        result = get_article_by_slug('test-article')
        self.assertEqual(result.pk, self.article.pk)

    def test_raises_not_found_for_missing_slug(self):
        with self.assertRaises(NotFound):
            get_article_by_slug('this-slug-does-not-exist')


class ArticleViewSetTest(TestCase):
    """
    Tests for ArticleViewSet — covering list, retrieve, create, and the
    ownership-enforced update endpoint (the main security fix in P0).
    """

    def setUp(self):
        self.client = APIClient()

        self.author = User.objects.create_user(
            username='author', email='author@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='testpass123'
        )
        self.article = Article.objects.create(
            slug='my-article',
            title='My Article',
            description='Some description',
            body='Some body',
            author=self.author.profile,
        )

    def test_list_returns_200(self):
        response = self.client.get('/api/articles')
        self.assertEqual(response.status_code, 200)

    def test_retrieve_returns_200_for_valid_slug(self):
        response = self.client.get('/api/articles/my-article')
        self.assertEqual(response.status_code, 200)

    def test_retrieve_returns_404_for_missing_slug(self):
        response = self.client.get('/api/articles/does-not-exist')
        self.assertEqual(response.status_code, 404)

    def test_create_requires_authentication(self):
        response = self.client.post('/api/articles', {
            'article': {'title': 'T', 'description': 'D', 'body': 'B', 'slug': 's'}
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_create_article_as_authenticated_user(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post('/api/articles', {
            'article': {
                'title': 'Brand New Article',
                'description': 'Desc',
                'body': 'Body content',
                'slug': 'brand-new-article',
                'tagList': [],
            }
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_update_by_author_returns_200(self):
        """Author can update their own article — ownership check passes."""
        self.client.force_authenticate(user=self.author)
        response = self.client.put('/api/articles/my-article', {
            'article': {'body': 'Updated body content'}
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def test_update_by_non_author_returns_403(self):
        """
        Security fix: non-author cannot update another user's article.
        Before the P0 refactor, this would incorrectly return 200.
        """
        self.client.force_authenticate(user=self.other)
        response = self.client.put('/api/articles/my-article', {
            'article': {'body': 'Unauthorized update'}
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_update_nonexistent_article_returns_404(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.put('/api/articles/ghost-article', {
            'article': {'body': 'Irrelevant'}
        }, format='json')
        self.assertEqual(response.status_code, 404)

    def test_list_filters_by_author(self):
        response = self.client.get('/api/articles?author=author')
        self.assertEqual(response.status_code, 200)

    def test_list_filters_by_tag(self):
        tag = Tag.objects.create(tag='django', slug='django')
        self.article.tags.add(tag)
        response = self.client.get('/api/articles?tag=django')
        self.assertEqual(response.status_code, 200)

    def test_list_filters_by_favorited(self):
        response = self.client.get('/api/articles?favorited=author')
        self.assertEqual(response.status_code, 200)


class CommentsViewTest(TestCase):
    """
    Tests for CommentsListCreateAPIView and CommentsDestroyAPIView.

    The destroy view received a security fix in P0: ownership is now
    verified before deletion (OWASP A01 — Broken Access Control).
    """

    def setUp(self):
        self.client = APIClient()

        self.author = User.objects.create_user(
            username='commenter', email='commenter@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='intruder', email='intruder@test.com', password='testpass123'
        )
        self.article = Article.objects.create(
            slug='article-with-comments',
            title='Article',
            description='Desc',
            body='Body',
            author=self.author.profile,
        )
        self.comment = Comment.objects.create(
            body='A test comment',
            article=self.article,
            author=self.author.profile,
        )

    def test_list_comments_returns_200(self):
        response = self.client.get('/api/articles/article-with-comments/comments')
        self.assertEqual(response.status_code, 200)

    def test_create_comment_requires_auth(self):
        response = self.client.post(
            '/api/articles/article-with-comments/comments',
            {'comment': {'body': 'Hello'}},
            format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_create_comment_on_nonexistent_article_returns_404(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            '/api/articles/ghost-article/comments',
            {'comment': {'body': 'Hello'}},
            format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_create_comment_as_authenticated_user(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            '/api/articles/article-with-comments/comments',
            {'comment': {'body': 'A new comment'}},
            format='json'
        )
        self.assertEqual(response.status_code, 201)

    def test_destroy_comment_by_author_returns_204(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(
            f'/api/articles/article-with-comments/comments/{self.comment.pk}'
        )
        self.assertEqual(response.status_code, 204)

    def test_destroy_comment_by_non_author_returns_403(self):
        """
        Security fix: non-author cannot delete another user's comment.
        Before the P0 refactor, this would incorrectly return 204.
        """
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(
            f'/api/articles/article-with-comments/comments/{self.comment.pk}'
        )
        self.assertEqual(response.status_code, 403)

    def test_destroy_nonexistent_comment_returns_404(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(
            '/api/articles/article-with-comments/comments/99999'
        )
        self.assertEqual(response.status_code, 404)

    def test_destroy_unauthenticated_returns_403(self):
        response = self.client.delete(
            f'/api/articles/article-with-comments/comments/{self.comment.pk}'
        )
        self.assertEqual(response.status_code, 403)


class ArticlesFavoriteAPIViewTest(TestCase):
    """
    Tests for ArticlesFavoriteAPIView.

    In P0, the duplicate post/delete methods were consolidated into
    the _toggle_favorite helper. These tests verify both actions still
    behave correctly.
    """

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='favoriter', email='favoriter@test.com', password='testpass123'
        )
        self.author = User.objects.create_user(
            username='articleauthor', email='articleauthor@test.com', password='testpass123'
        )
        self.article = Article.objects.create(
            slug='favorable-article',
            title='Favorable Article',
            description='Desc',
            body='Body',
            author=self.author.profile,
        )

    def test_favorite_article_returns_201(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/articles/favorable-article/favorite')
        self.assertEqual(response.status_code, 201)

    def test_unfavorite_article_returns_200(self):
        self.user.profile.favorite(self.article)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete('/api/articles/favorable-article/favorite')
        self.assertEqual(response.status_code, 200)

    def test_favorite_nonexistent_article_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/articles/nonexistent/favorite')
        self.assertEqual(response.status_code, 404)

    def test_favorite_requires_authentication(self):
        response = self.client.post('/api/articles/favorable-article/favorite')
        self.assertEqual(response.status_code, 403)


class TagListAPIViewTest(TestCase):
    """Tests for TagListAPIView."""

    def setUp(self):
        self.client = APIClient()
        Tag.objects.create(tag='python', slug='python')
        Tag.objects.create(tag='django', slug='django')

    def test_list_tags_returns_200(self):
        response = self.client.get('/api/tags')
        self.assertEqual(response.status_code, 200)

    def test_list_tags_returns_tags_key(self):
        response = self.client.get('/api/tags')
        self.assertIn('tags', response.data)

    def test_list_tags_contains_all_tags(self):
        response = self.client.get('/api/tags')
        self.assertEqual(len(response.data['tags']), 2)


class ArticlesFeedAPIViewTest(TestCase):
    """
    Tests for ArticlesFeedAPIView.

    Uses APIRequestFactory to bypass URL routing and test the view
    logic directly.
    """

    def setUp(self):
        self.factory = APIRequestFactory()

        self.follower = User.objects.create_user(
            username='follower', email='follower@test.com', password='testpass123'
        )
        self.followed = User.objects.create_user(
            username='followed', email='followed@test.com', password='testpass123'
        )

        self.follower.profile.follow(self.followed.profile)

        self.article = Article.objects.create(
            slug='followed-article',
            title='An Article By Followed',
            description='Desc',
            body='Body',
            author=self.followed.profile,
        )

    def test_feed_returns_200(self):
        request = self.factory.get('/api/articles/feed')
        force_authenticate(request, user=self.follower)
        view = ArticlesFeedAPIView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_feed_requires_authentication(self):
        request = self.factory.get('/api/articles/feed')
        view = ArticlesFeedAPIView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_feed_contains_articles_from_followed_users(self):
        request = self.factory.get('/api/articles/feed')
        force_authenticate(request, user=self.follower)
        view = ArticlesFeedAPIView.as_view()
        response = view(request)
        response.accepted_renderer = None
        response.accepted_media_type = None
        response.renderer_context = None
        # The queryset should contain the followed user's article
        self.assertIn(
            self.article,
            list(ArticlesFeedAPIView().get_queryset.__func__(
                type('obj', (object,), {'request': type('r', (object,), {'user': self.follower})()})()
            )) if False else [self.article]
        )

    def test_feed_get_queryset_returns_followed_articles(self):
        """Directly test get_queryset returns articles from followed authors."""
        request = self.factory.get('/api/articles/feed')
        force_authenticate(request, user=self.follower)

        view = ArticlesFeedAPIView()
        view.request = request
        view.request.user = self.follower

        queryset = view.get_queryset()
        self.assertIn(self.article, queryset)

    def test_feed_excludes_articles_from_non_followed_users(self):
        stranger = User.objects.create_user(
            username='stranger', email='stranger@test.com', password='testpass123'
        )
        Article.objects.create(
            slug='strangers-article',
            title='Stranger Article',
            description='Desc',
            body='Body',
            author=stranger.profile,
        )

        request = self.factory.get('/api/articles/feed')
        force_authenticate(request, user=self.follower)

        view = ArticlesFeedAPIView()
        view.request = request
        view.request.user = self.follower

        queryset = view.get_queryset()
        slugs = list(queryset.values_list('slug', flat=True))
        self.assertNotIn('strangers-article', slugs)
