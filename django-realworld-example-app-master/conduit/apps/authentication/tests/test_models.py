from django.test import TestCase

from conduit.apps.authentication.models import User


class UserManagerTest(TestCase):
    """Tests for UserManager — the custom manager for the User model."""

    def test_create_user_returns_user_instance(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.assertIsInstance(user, User)

    def test_create_user_sets_email(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_create_user_sets_username(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        # The stored password must not be the plain-text password
        self.assertNotEqual(user.password, 'testpass123')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_user_raises_without_username(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(
                username=None, email='test@example.com', password='testpass123'
            )

    def test_create_user_raises_without_email(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(
                username='testuser', email=None, password='testpass123'
            )

    def test_create_superuser_sets_is_staff(self):
        user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpass123'
        )
        self.assertTrue(user.is_staff)

    def test_create_superuser_sets_is_superuser(self):
        user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpass123'
        )
        self.assertTrue(user.is_superuser)

    def test_create_superuser_raises_without_password(self):
        with self.assertRaises(TypeError):
            User.objects.create_superuser(
                username='admin', email='admin@example.com', password=None
            )


class UserModelTest(TestCase):
    """Tests for the User model, focusing on the token property bridge."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser', email='modeluser@test.com', password='testpass123'
        )

    def test_token_property_returns_string(self):
        """
        User.token is a Strangler Fig bridge to TokenService.generate_token().
        It must return a valid JWT string.
        """
        self.assertIsInstance(self.user.token, str)

    def test_token_property_is_non_empty(self):
        self.assertTrue(len(self.user.token) > 0)

    def test_str_returns_email(self):
        self.assertEqual(str(self.user), 'modeluser@test.com')

    def test_get_full_name_returns_username(self):
        self.assertEqual(self.user.get_full_name(), 'modeluser')

    def test_get_short_name_returns_username(self):
        self.assertEqual(self.user.get_short_name(), 'modeluser')

    def test_signal_auto_creates_profile(self):
        """
        A Profile must be auto-created via post_save signal when a User is
        created — required for the author FK on Article and Comment.
        """
        from conduit.apps.profiles.models import Profile
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
