from django.db import transaction

from rest_framework import serializers

from conduit.apps.profiles.serializers import ProfileSerializer

from .models import User
from .services import AuthenticationService, TokenService


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializers registration requests and creates a new user."""

    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'token']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Handles login validation. Authentication logic is delegated to
    AuthenticationService (SRP): this serializer only validates input
    format and translates service-layer errors into DRF validation errors.
    """
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)

        try:
            user = AuthenticationService.authenticate(email, password)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

        return {
            'email': user.email,
            'username': user.username,
            'token': TokenService.generate_token(user)
        }


class UserSerializer(serializers.ModelSerializer):
    """Handles serialization and deserialization of User objects."""

    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    profile = ProfileSerializer(write_only=True)

    bio = serializers.CharField(source='profile.bio', read_only=True)
    image = serializers.CharField(source='profile.image', read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'token', 'profile', 'bio',
            'image',
        )

        read_only_fields = ('token',)

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Performs an update on a User.

        Wrapped in @transaction.atomic to ensure that if the profile save
        fails, the user changes are rolled back too. Without this, a
        failure on instance.profile.save() would leave the user partially
        updated — violating the Atomicity property.
        """
        password = validated_data.pop('password', None)
        profile_data = validated_data.pop('profile', {})

        for (key, value) in validated_data.items():
            setattr(instance, key, value)

        if password is not None:
            instance.set_password(password)

        instance.save()

        for (key, value) in profile_data.items():
            setattr(instance.profile, key, value)

        instance.profile.save()

        return instance
