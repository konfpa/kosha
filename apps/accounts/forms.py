from django import forms
from django.contrib.auth import forms as auth_forms

from .models import User


class UserCreationForm(auth_forms.AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name")


class UserChangeForm(auth_forms.UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


class LoginForm(auth_forms.AuthenticationForm):
    remember = forms.BooleanField(required=False, initial=True)

    error_messages = {
        **auth_forms.AuthenticationForm.error_messages,
        "invalid_login": (
            "That email and password don't match an account. Check them and try again."
        ),
    }
