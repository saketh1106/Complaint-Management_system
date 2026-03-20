from django.contrib.auth.backends import ModelBackend
from .models import CustomUser

class OrganizationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, organization=None, **kwargs):
        try:
            # This is the fix: We filter by BOTH username and organization
            user = CustomUser.objects.get(username=username, organization=organization)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except (CustomUser.DoesNotExist, CustomUser.MultipleObjectsReturned):
            return None