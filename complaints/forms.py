#forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Complaint, Organization

# ======================================
# COMPLAINT FORM
# ======================================
class ComplaintForm(forms.ModelForm):
    file = forms.FileField(required=False)
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'priority']


# ======================================
# STAFF / SUPERADMIN CREATION FORM
# ======================================
# complaints/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class StaffCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        # We pop 'organization' so it doesn't break the standard UserCreationForm
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        # Remove global unique validator to allow same usernames in DIFFERENT orgs
        if 'username' in self.fields:
            self.fields['username'].validators = []

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Check if username exists ONLY inside THIS organization
        if CustomUser.objects.filter(
            username=username, 
            organization=self.organization
        ).exists():
            raise forms.ValidationError("This username already exists in your organization.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.organization = self.organization  # CRITICAL: Attach the org here
        user.is_staff = True
        user.is_superuser = False
        
        if commit:
            user.save()
        return user

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class SuperAdminCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ("username", "password1", "password2")