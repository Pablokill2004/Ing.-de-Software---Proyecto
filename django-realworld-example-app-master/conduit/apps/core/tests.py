from django.test import TestCase

from conduit.apps.core.utils import generate_random_string, DEFAULT_CHAR_STRING
from conduit.apps.authentication.models import User


class GenerateRandomStringTest(TestCase):
    def test_default_length(self):
        result = generate_random_string()
        self.assertEqual(len(result), 6)

    def test_custom_length(self):
        result = generate_random_string(size=10)
        self.assertEqual(len(result), 10)

    def test_characters_from_charset(self):
        result = generate_random_string()
        for char in result:
            self.assertIn(char, DEFAULT_CHAR_STRING)

    def test_custom_charset(self):
        result = generate_random_string(chars='abc', size=5)
        for char in result:
            self.assertIn(char, 'abc')


class TimestampedModelTest(TestCase):
    def test_created_at_and_updated_at(self):
        user = User.objects.create_user(
            username='coreuser', email='core@example.com', password='testpass123'
        )
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        self.assertLessEqual(user.created_at, user.updated_at)
