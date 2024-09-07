from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, LoginForm
from .models import UserRole

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'vm/register.html', {'form': form})

def login(request):
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
    return render(request, 'vm/login.html', {'form': form})

@login_required
def home(request):
    if request.user.role == UserRole.ADMIN:
        # Admin-specific logic
        pass
    elif request.user.role == UserRole.STANDARD_USER:
        # Standard user-specific logic
        pass
    elif request.user.role == UserRole.GUEST:
        # Guest-specific logic
        pass
    return render(request, 'vm/home.html')