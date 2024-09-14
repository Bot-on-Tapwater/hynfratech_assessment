from django.db import models
from django.contrib.auth.models import AbstractUser

class UserRole(models.TextChoices):
    ADMIN = 'Admin', 'Admin'
    STANDARD_USER = 'Standard User', 'Standard User'
    GUEST = 'Guest', 'Guest'

class CustomUser(AbstractUser):
    role = models.CharField(max_length=50, choices=UserRole.choices, default=UserRole.STANDARD_USER)

# Add any other fields you need for the user model.
