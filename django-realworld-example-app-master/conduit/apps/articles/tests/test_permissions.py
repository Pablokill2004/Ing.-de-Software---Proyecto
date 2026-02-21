from django.test import TestCase
from unittest.mock import MagicMock

from rest_framework.test import APIRequestFactory

from conduit.apps.articles.permissions import IsAuthorOrReadOnly
from conduit.apps.authentication.models import User


class IsAuthorOrReadOnlyPermissionTest(TestCase):
    """
    Tests for the IsAuthorOrReadOnly permission class.

    This permission implements the Strategy Pattern via DRF's permission
    framework. It allows safe (read) methods for everyone, and restricts
    write methods to the object's author only.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAuthorOrReadOnly()

        self.author = User.objects.create_user(
            username='author', email='author@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='testpass123'
        )

    def _make_request(self, method, user):
        request = getattr(self.factory, method)('/')
        request.user = user
        return request

    # --- Safe methods: always allowed regardless of ownership ---

    def test_get_is_always_allowed(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('get', self.other)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_head_is_always_allowed(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('head', self.other)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_options_is_always_allowed(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('options', self.other)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    # --- Write methods: only allowed for the author ---

    def test_put_allowed_for_author(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('put', self.author)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_patch_allowed_for_author(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('patch', self.author)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_delete_allowed_for_author(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('delete', self.author)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    # --- Write methods: denied for non-authors ---

    def test_put_denied_for_non_author(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('put', self.other)
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_patch_denied_for_non_author(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('patch', self.other)
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_delete_denied_for_non_author(self):
        obj = MagicMock()
        obj.author = self.author.profile
        request = self._make_request('delete', self.other)
        self.assertFalse(self.permission.has_object_permission(request, None, obj))
