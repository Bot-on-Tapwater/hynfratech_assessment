from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

"""
Compromises:
    - Proper input validation
"""

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
