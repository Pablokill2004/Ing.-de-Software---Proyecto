from django.test import TestCase

from conduit.apps.authentication.models import User
from conduit.apps.profiles.models import Profile
from conduit.apps.profiles.exceptions import ProfileDoesNotExist


class ProfileCreationTest(TestCase):
    def test_profile_created_on_user_save(self):
        user = User.objects.create_user(
            username='profileuser', email='profile@example.com', password='testpass123'
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str(self):
        user = User.objects.create_user(
            username='struser', email='str@example.com', password='testpass123'
        )
        profile = Profile.objects.get(user=user)
        self.assertEqual(str(profile), 'struser')

    def test_profile_follow_and_unfollow(self):
        user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='testpass123'
        )
        user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='testpass123'
        )
        p1 = Profile.objects.get(user=user1)
        p2 = Profile.objects.get(user=user2)
        p1.follow(p2)
        self.assertTrue(p1.is_following(p2))
        self.assertTrue(p2.is_followed_by(p1))
        p1.unfollow(p2)
        self.assertFalse(p1.is_following(p2))


class ProfileDoesNotExistTest(TestCase):
    def test_exception_status_code(self):
        exc = ProfileDoesNotExist()
        self.assertEqual(exc.status_code, 400)

    def test_exception_default_detail(self):
        exc = ProfileDoesNotExist()
        self.assertIn('profile', str(exc.default_detail).lower())
