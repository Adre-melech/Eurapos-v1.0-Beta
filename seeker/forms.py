from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Seeker
from jobs.models import SeekerCountry, JobTitle
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

class SeekerRegistrationForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=True)
    country = forms.ModelChoiceField(queryset=SeekerCountry.objects.all(), required=True)
    job_title = forms.ModelChoiceField(queryset=JobTitle.objects.all(), required=True)

    class Meta:
        model = Seeker
        fields = ['username', 'email', 'phone', 'country', 'job_title', 'password1', 'password2']


class SeekerEditForm(forms.ModelForm):
    """Allows admins to edit a seeker profile"""
    phone = forms.CharField(max_length=15, required=True)
    country = forms.ModelChoiceField(queryset=SeekerCountry.objects.all(), required=True)
    job_title = forms.ModelChoiceField(queryset=JobTitle.objects.all(), required=True)

    class Meta:
        model = Seeker
        fields = ['username', 'email', 'phone', 'country', 'job_title']


class SeekerPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        print(f"Searching for: {email}")
        users = get_user_model().objects.filter(email__iexact=email, is_active=True)
        print(f"Found: {[user.email for user in users]}")
        return users
