from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Object-level permission that allows write operations only if the
    requesting user is the author of the object.

    This implements the Strategy Pattern via DRF's permission framework —
    authorization logic is encapsulated in an interchangeable strategy class
    rather than being hard-coded into each view method.

    Addresses OWASP A01 (Broken Access Control): without this permission,
    any authenticated user could update or delete content they do not own.
    """

    message = 'You must be the author of this content to modify it.'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # Articles have an `author` field (Profile instance).
        # Comments also have an `author` field (Profile instance).
        return obj.author == request.user.profile
