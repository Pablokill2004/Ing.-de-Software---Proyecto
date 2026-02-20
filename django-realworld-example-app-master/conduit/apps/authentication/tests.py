from django.test import TestCase

from conduit.apps.authentication.models import User, UserManager


class UserManagerTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_user_no_username_raises(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(username=None, email='test@example.com')

    def test_create_user_no_email_raises(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(username='testuser', email=None)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_superuser_no_password_raises(self):
        with self.assertRaises(TypeError):
            User.objects.create_superuser(
                username='admin', email='admin@example.com', password=None
            )


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser', email='model@example.com', password='testpass123'
        )

    def test_str(self):
        self.assertEqual(str(self.user), 'model@example.com')

    def test_get_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'modeluser')

    def test_get_short_name(self):
        self.assertEqual(self.user.get_short_name(), 'modeluser')

    def test_token_is_string(self):
        token = self.user.token
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)
