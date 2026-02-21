import jwt

from django.conf import settings
from django.test import TestCase

from conduit.apps.authentication.models import User
from conduit.apps.authentication.services import AuthenticationService, TokenService


class TokenServiceTest(TestCase):
    """
    Tests for TokenService — the extracted JWT generation service.

    Verifies the two bugs fixed in the tech debt refactoring:
    - Portability: uses datetime.timestamp() instead of strftime('%s').
    - PyJWT compatibility: handles both str (>= 2.0) and bytes (< 2.0) return types.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='tokenuser', email='tokenuser@test.com', password='testpass123'
        )

    def test_generate_token_returns_string(self):
        token = TokenService.generate_token(self.user)
        self.assertIsInstance(token, str)

    def test_generated_token_is_not_empty(self):
        token = TokenService.generate_token(self.user)
        self.assertTrue(len(token) > 0)

    def test_token_contains_user_id(self):
        token = TokenService.generate_token(self.user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(payload['id'], self.user.pk)

    def test_token_contains_expiry(self):
        token = TokenService.generate_token(self.user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertIn('exp', payload)

    def test_token_uses_hs256_algorithm(self):
        token = TokenService.generate_token(self.user)
        header = jwt.get_unverified_header(token)
        self.assertEqual(header['alg'], 'HS256')

    def test_different_users_get_different_tokens(self):
        other = User.objects.create_user(
            username='other', email='other@test.com', password='testpass123'
        )
        token1 = TokenService.generate_token(self.user)
        token2 = TokenService.generate_token(other)
        self.assertNotEqual(token1, token2)


class AuthenticationServiceTest(TestCase):
    """
    Tests for AuthenticationService — the extracted login logic.

    Before this extraction, these responsibilities lived inside
    LoginSerializer.validate, violating the Single Responsibility Principle.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser', email='authuser@test.com', password='testpass123'
        )

    def test_authenticate_returns_user_with_valid_credentials(self):
        result = AuthenticationService.authenticate('authuser@test.com', 'testpass123')
        self.assertEqual(result, self.user)

    def test_authenticate_raises_on_missing_email(self):
        with self.assertRaises(ValueError) as ctx:
            AuthenticationService.authenticate(None, 'testpass123')
        self.assertIn('email', str(ctx.exception).lower())

    def test_authenticate_raises_on_empty_email(self):
        with self.assertRaises(ValueError):
            AuthenticationService.authenticate('', 'testpass123')

    def test_authenticate_raises_on_missing_password(self):
        with self.assertRaises(ValueError) as ctx:
            AuthenticationService.authenticate('authuser@test.com', None)
        self.assertIn('password', str(ctx.exception).lower())

    def test_authenticate_raises_on_empty_password(self):
        with self.assertRaises(ValueError):
            AuthenticationService.authenticate('authuser@test.com', '')

    def test_authenticate_raises_on_wrong_password(self):
        with self.assertRaises(ValueError) as ctx:
            AuthenticationService.authenticate('authuser@test.com', 'wrongpassword')
        self.assertIn('not found', str(ctx.exception).lower())

    def test_authenticate_raises_on_nonexistent_email(self):
        with self.assertRaises(ValueError):
            AuthenticationService.authenticate('nobody@test.com', 'testpass123')

    def test_authenticate_raises_for_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        with self.assertRaises(ValueError) as ctx:
            AuthenticationService.authenticate('authuser@test.com', 'testpass123')
        self.assertIn('deactivated', str(ctx.exception).lower())
