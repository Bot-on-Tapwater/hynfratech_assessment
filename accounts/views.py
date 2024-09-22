import os
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
import requests
from .forms import CustomUserCreationForm, LoginForm
from .models import UserRole
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
# from google.auth.transport import requests
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from google.auth.transport import requests as google_requests
from django.contrib.auth import logout as auth_logout
from functools import wraps

def admin_required(view_func):
    """
    Decorator to check if the user is an admin.
    If not, they are redirected to the 'access_denied' page.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        
        if request.user.role == UserRole.ADMIN:
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to an 'Access Denied' page or another page (e.g., home)
            return redirect(reverse('access_denied'))  # Replace with the URL of your choice
    return _wrapped_view

def admin_or_standard_user_required(view_func):
    """
    Decorator to check if the user is either an admin or a standard user.
    If not, they are redirected to the 'access_denied' page.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        
        if request.user.role in [UserRole.ADMIN, UserRole.STANDARD_USER]:
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to an 'Access Denied' page or another page (e.g., home)
            return redirect(reverse('access_denied'))  # Replace with the URL of your choice
    return _wrapped_view

def access_denied(request):
    """
    Render an 'Access Denied' page with a generic message.

    This view is called when a user tries to access a page that requires a certain role or permission that they don't have.
    The view renders a template with the message "You don't have permission to access this page.".
    """
    return render(request, 'accounts/access_denied.html', {
        'error': "You don't have permission to access this page."
    })

def register(request):
    """
    Handles user registration.

    If the request is a GET, it renders a template with a form to register a new user.
    If the request is a POST, it validates the form and creates a new user if the form is valid.
    If the user is created successfully, it redirects to the login page.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    role_choices = UserRole.choices
    return render(request, 'accounts/register_clean.html', {'form': form, 'role_choices': role_choices})

@csrf_exempt
def login(request):
    """
    Handles user login.

    If the request is a GET, it renders a template with a form to log in.
    If the request is a POST, it validates the form and logs in the user if the form is valid.
    If the user is logged in successfully, it redirects to the home page.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                auth_login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'accounts/login_clean.html', {'form': form})

def home(request):
    """
    Displays the home page.

    This view is accessible to all users (anonymous and authenticated).
    It renders a template with a greeting message.
    """
    return render(request, 'accounts/home_clean.html')

@csrf_exempt
def google_complete(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    token = request.POST.get('credential')

    try:
        # Verify the token using the correct 'Request' from google.auth.transport
        user_data = id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )
        email = user_data.get('email')
        first_name = user_data.get('given_name')
        last_name = user_data.get('family_name')

        # Get or create the user in the database
        User = get_user_model()
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email,  # Username can be set as email
            'first_name': first_name,
            'last_name': last_name,
            'role': UserRole.STANDARD_USER  # Default role as GUEST
        })

        # Log the user in
        auth_login(request, user)

    except ValueError:
        return HttpResponse(status=403)

    return redirect('home')

@login_required
def logout(request):
    """
    Logs out the user (Custom or Google) and redirects to the login page.
    """
    auth_logout(request)  # This will log out any authenticated user
    return redirect('home')