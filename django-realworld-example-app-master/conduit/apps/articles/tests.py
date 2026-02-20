from django.test import TestCase

from conduit.apps.authentication.models import User
from conduit.apps.profiles.models import Profile
from conduit.apps.articles.models import Article, Tag


def make_user(username='articleuser', email='article@example.com'):
    return User.objects.create_user(
        username=username, email=email, password='testpass123'
    )


class TagModelTest(TestCase):
    def test_tag_str(self):
        tag = Tag.objects.create(tag='python', slug='python')
        self.assertEqual(str(tag), 'python')


class ArticleModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.profile = Profile.objects.get(user=self.user)

    def test_article_str(self):
        article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            description='A test article',
            body='Body text',
            author=self.profile,
        )
        self.assertEqual(str(article), 'Test Article')

    def test_article_slug_auto_generated(self):
        article = Article(
            title='My Test Post',
            description='desc',
            body='body',
            author=self.profile,
        )
        article.save()
        self.assertTrue(len(article.slug) > 0)
        self.assertIn('my-test-post', article.slug)

    def test_article_long_title_slug_truncated(self):
        long_title = 'word ' * 60
        article = Article(
            title=long_title,
            description='desc',
            body='body',
            author=self.profile,
        )
        article.save()
        self.assertLessEqual(len(article.slug), 255)

    def test_article_slug_single_word(self):
        article = Article(
            title='Supercalifragilistic' * 15,
            description='desc',
            body='body',
            author=self.profile,
        )
        article.save()
        self.assertLessEqual(len(article.slug), 255)

    def test_article_with_tags(self):
        tag = Tag.objects.create(tag='django', slug='django')
        article = Article.objects.create(
            title='Tagged Article',
            slug='tagged-article',
            description='desc',
            body='body',
            author=self.profile,
        )
        article.tags.add(tag)
        self.assertIn(tag, article.tags.all())
