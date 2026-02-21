from unittest.mock import patch

from django.test import TestCase

from rest_framework.exceptions import ValidationError

from conduit.apps.authentication.models import User
from conduit.apps.authentication.serializers import (
    LoginSerializer, RegistrationSerializer, UserSerializer
)


class RegistrationSerializerTest(TestCase):
    """Tests for RegistrationSerializer."""

    def test_valid_data_creates_user(self):
        serializer = RegistrationSerializer(data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'strongpass123',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, 'newuser@test.com')

    def test_token_is_present_in_output(self):
        serializer = RegistrationSerializer(data={
            'username': 'tokencheck',
            'email': 'tokencheck@test.com',
            'password': 'strongpass123',
        })
        serializer.is_valid()
        user = serializer.save()
        self.assertIn('token', serializer.data)

    def test_password_too_short_is_invalid(self):
        serializer = RegistrationSerializer(data={
            'username': 'shortpass',
            'email': 'shortpass@test.com',
            'password': '123',
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_duplicate_email_is_invalid(self):
        User.objects.create_user(
            username='existing', email='dup@test.com', password='testpass123'
        )
        serializer = RegistrationSerializer(data={
            'username': 'newuser2',
            'email': 'dup@test.com',
            'password': 'testpass123',
        })
        self.assertFalse(serializer.is_valid())


class LoginSerializerTest(TestCase):
    """
    Tests for the refactored LoginSerializer.

    After the P2 refactor, validate() delegates to AuthenticationService.
    It now has a single responsibility: translating service errors into
    DRF ValidationErrors.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', email='loginuser@test.com', password='testpass123'
        )

    def test_valid_credentials_return_token(self):
        serializer = LoginSerializer(data={
            'email': 'loginuser@test.com',
            'password': 'testpass123',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn('token', serializer.validated_data)

    def test_valid_credentials_return_email(self):
        serializer = LoginSerializer(data={
            'email': 'loginuser@test.com',
            'password': 'testpass123',
        })
        serializer.is_valid()
        self.assertEqual(serializer.validated_data['email'], 'loginuser@test.com')

    def test_valid_credentials_return_username(self):
        serializer = LoginSerializer(data={
            'email': 'loginuser@test.com',
            'password': 'testpass123',
        })
        serializer.is_valid()
        self.assertEqual(serializer.validated_data['username'], 'loginuser')

    def test_wrong_password_raises_validation_error(self):
        serializer = LoginSerializer(data={
            'email': 'loginuser@test.com',
            'password': 'wrongpassword',
        })
        self.assertFalse(serializer.is_valid())

    def test_nonexistent_user_raises_validation_error(self):
        serializer = LoginSerializer(data={
            'email': 'nobody@test.com',
            'password': 'testpass123',
        })
        self.assertFalse(serializer.is_valid())

    def test_missing_email_raises_validation_error(self):
        serializer = LoginSerializer(data={'password': 'testpass123'})
        self.assertFalse(serializer.is_valid())

    def test_missing_password_raises_validation_error(self):
        serializer = LoginSerializer(data={'email': 'loginuser@test.com'})
        self.assertFalse(serializer.is_valid())

    def test_inactive_user_raises_validation_error(self):
        self.user.is_active = False
        self.user.save()

        serializer = LoginSerializer(data={
            'email': 'loginuser@test.com',
            'password': 'testpass123',
        })
        self.assertFalse(serializer.is_valid())


class UserSerializerTest(TestCase):
    """
    Tests for UserSerializer.update — specifically the @transaction.atomic
    fix that ensures user and profile saves are atomic.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='updateuser', email='updateuser@test.com', password='testpass123'
        )

    def test_update_changes_username(self):
        serializer = UserSerializer(
            instance=self.user,
            data={
                'username': 'updatedname',
                'email': self.user.email,
                'profile': {'bio': ''},
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updatedname')

    def test_update_changes_profile_bio(self):
        serializer = UserSerializer(
            instance=self.user,
            data={
                'username': self.user.username,
                'email': self.user.email,
                'profile': {'bio': 'My new bio'},
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'My new bio')

    def test_update_changes_password(self):
        serializer = UserSerializer(
            instance=self.user,
            data={
                'username': self.user.username,
                'email': self.user.email,
                'password': 'newstrongpass123',
                'profile': {'bio': ''},
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newstrongpass123'))

    def test_update_is_atomic_rolls_back_on_profile_save_failure(self):
        """
        If profile.save() raises an exception, the user.save() must also
        be rolled back. This verifies the @transaction.atomic guarantee.
        """
        original_username = self.user.username

        with patch.object(
            self.user.profile.__class__, 'save',
            side_effect=Exception('Simulated profile save failure')
        ):
            serializer = UserSerializer(
                instance=self.user,
                data={
                    'username': 'should-be-rolled-back',
                    'email': self.user.email,
                    'profile': {'bio': 'should also roll back'},
                },
                partial=True,
            )
            serializer.is_valid()

            with self.assertRaises(Exception):
                serializer.save()

        self.user.refresh_from_db()
        self.assertEqual(
            self.user.username, original_username,
            'Username should have been rolled back by @transaction.atomic'
        )
