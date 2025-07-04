from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Seeker
from jobs.models import SeekerCountry, JobTitle
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

from django import forms
from django.contrib.auth.forms import UserCreationForm
from seeker.models import Seeker
from jobs.models import SeekerCountry, JobTitle


class SeekerRegistrationForm(UserCreationForm):
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Enter your phone number"})
    )
    country = forms.ModelChoiceField(
        queryset=SeekerCountry.objects.all(),
        required=True,
        widget=forms.Select(attrs={"placeholder": "Select your country"})
    )
    job_title = forms.ModelChoiceField(
        queryset=JobTitle.objects.all(),
        required=True,
        widget=forms.Select(attrs={"placeholder": "Select your desired job title"})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Enter a valid email address"})
    )

    class Meta:
        model = Seeker
        fields = ['username', 'email', 'phone', 'country', 'job_title', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({"placeholder": "Choose a unique username"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Minimum 4 characters"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Repeat password"})

        # ✅ Suppress default help text on password fields
        self.fields["username"].help_text = None
        self.fields["password1"].help_text = None
        self.fields["password2"].help_text = None

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if Seeker.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists. Try adding numbers or symbols.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Seeker.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use. Try a different one.")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 4:
            raise forms.ValidationError("Password must be at least 4 characters long.")
        return password1


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


class ATSCVUploadForm(forms.Form):
    cv_file = forms.FileField(
        label="Upload your current CV",
        required=True,
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx"})
    )