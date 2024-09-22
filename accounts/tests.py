from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model  # Import this to get the custom user model
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

CustomUser = get_user_model()  # This will refer to CustomUser instead of the default User model

class UserViewsTestCase(TestCase):
    def setUp(self):
        """
        Set up the test client and the user and URLs to be tested

        This method is called before every test and creates the test client,
        a test user, and the URLs for the register, login, and home views.
        """
        self.client = APIClient()
        self.username = 'testuser'
        self.password = 'securepassword'
        self.user = CustomUser.objects.create_user(username=self.username, password=self.password)
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.home_url = reverse('home')

    def test_register_view(self):
        """
        Test that the register view works correctly.

        Should create a new user in the database and redirect after successful registration.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',  # Ensure you include the email field
            'role': 'Admin',  # Or any role that your form expects
            'password1': 'TwoGreen1.',
            'password2': 'TwoGreen1.',
        })

        if response.status_code == 200:
            print(response.content)  # Print the response content for debugging
        
        self.assertEqual(response.status_code, 302)  # Redirects after successful registration


    def test_login_view(self):
        """
        Test that the login view works correctly.

        Should redirect after successful login.
        """
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password,
        })
        self.assertEqual(response.status_code, 302)  # Redirects after successful login

    def test_home_view(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)  # Home page should be accessible
