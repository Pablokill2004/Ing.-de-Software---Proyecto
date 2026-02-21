import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate as django_authenticate


class TokenService:
    """
    Encapsulates JWT token generation — extracted from the User model
    to satisfy the Single Responsibility Principle (SRP).

    Before this extraction, the User model had two reasons to change:
    (1) user schema changes, and (2) token strategy changes (algorithm,
    claims, expiry). Now each concern lives in its own class.

    This follows the Service Layer Pattern and the Extract Class
    refactoring technique.

    Fixes applied:
    - Replaced strftime('%s') with datetime.timestamp() for Windows
      portability (strftime '%s' is a platform-specific extension that
      raises ValueError on Windows).
    - Handles both PyJWT < 2.0 (returns bytes) and >= 2.0 (returns str),
      preventing AttributeError on .decode('utf-8').
    """

    TOKEN_EXPIRY_DAYS = 60
    ALGORITHM = 'HS256'

    @classmethod
    def generate_token(cls, user):
        """Generate a JWT token for the given user."""
        dt = datetime.now() + timedelta(days=cls.TOKEN_EXPIRY_DAYS)

        payload = {
            'id': user.pk,
            'exp': int(dt.timestamp())
        }

        token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=cls.ALGORITHM
        )

        # PyJWT >= 2.0 returns str; < 2.0 returns bytes.
        if isinstance(token, bytes):
            return token.decode('utf-8')

        return token


class AuthenticationService:
    """
    Encapsulates authentication logic — extracted from LoginSerializer.validate
    to satisfy SRP.

    The LoginSerializer was doing three things: input validation, authentication,
    and response shaping. Now authentication lives here, and the serializer
    only handles validation and serialization.
    """

    @staticmethod
    def authenticate(email, password):
        """
        Authenticate a user by email and password.

        Raises ValueError with a descriptive message on failure, allowing
        the caller (serializer) to translate it into the appropriate
        framework-specific error response.
        """
        if not email:
            raise ValueError('An email address is required to log in.')

        if not password:
            raise ValueError('A password is required to log in.')

        user = django_authenticate(username=email, password=password)

        if user is None:
            raise ValueError(
                'A user with this email and password was not found.'
            )

        if not user.is_active:
            raise ValueError('This user has been deactivated.')

        return user
