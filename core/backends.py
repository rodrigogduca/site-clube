from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameBackend(ModelBackend):
    """Allow login with either username or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        # Try by username first
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Try by email
            try:
                user = User.objects.get(email=username)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
