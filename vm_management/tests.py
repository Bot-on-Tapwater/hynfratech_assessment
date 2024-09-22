from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from unittest.mock import patch
from .models import VM, Subscription, RatePlan, Payment, Backup, ActionLog
from django.core.mail import send_mail
from accounts.models import CustomUser
import paramiko

User = get_user_model()

class VMManagementTests(TestCase):
    def setUp(self):
        
    # Create a test user with a subscription and log them in, creating the necessary objects.
    # This is done for every test in the class, so that we have a clean slate.
    # The user is given a 30-day subscription, which is active.
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.rate_plan = RatePlan.objects.create(name='Bronze', price=100, max_vms=1, max_backups=1)
        self.subscription = Subscription.objects.create(user=self.user, rate_plan=self.rate_plan, active=True, start_date=timezone.now(), end_date=timezone.now() + timedelta(days=30))

    @patch('vm_management.views.run_vboxmanage_command')
    def test_create_vm_success(self, mock_run_command):
        """
        Test that creating a VM with valid data works correctly.
        Should create a VM object and a pending payment.
        """
        mock_run_command.return_value = 'Command executed successfully'
        response = self.client.post(reverse('create_vm'), {'name': 'testvm', 'disk_size': 2048, 'cpu': 2, 'memory': 512})
        
        self.assertEqual(response.status_code, 302)  # Redirects after success
        self.assertTrue(VM.objects.filter(name='testvm').exists())
        self.assertTrue(Payment.objects.filter(user=self.user, status='pending').exists())

    @patch('vm_management.views.run_vboxmanage_command')
    def test_start_vm(self, mock_run_command):
        """
        Test that starting a VM with a valid ID works correctly.
        Should change the VM status to 'running' and log the action.
        """
        mock_run_command.return_value = 'Command executed successfully'
        vm = VM.objects.create(name='testvm', user=self.user, disk_size=1024, status='stopped', cpu=1, memory=256, price=0)
        
        response = self.client.get(reverse('start_vm', args=[vm.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects after starting VM
        vm.refresh_from_db()
        self.assertEqual(vm.status, 'running')
        self.assertTrue(ActionLog.objects.filter(action_type='start', vm=vm, user=self.user).exists())

    @patch('vm_management.views.run_vboxmanage_command')
    def test_stop_vm(self, mock_run_command):
        """
        Test that stopping a VM with a valid ID works correctly.
        Should change the VM status to 'stopped' and log the action.
        """
        mock_run_command.return_value = 'Command executed successfully'
        vm = VM.objects.create(name='testvm', user=self.user, disk_size=1024, status='running', cpu=1, memory=256, price=0)
        
        response = self.client.get(reverse('stop_vm', args=[vm.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects after stopping VM
        vm.refresh_from_db()
        self.assertEqual(vm.status, 'stopped')
        self.assertTrue(ActionLog.objects.filter(action_type='stop', vm=vm, user=self.user).exists())

    @patch('vm_management.views.send_smtp_email')
    def test_payment_page(self, mock_send_email):
        """
        Test that the payment page works correctly.
        Should create a payment entry with status 'completed', and activate the user's subscription.
        """
        mock_send_email.return_value = None
        response = self.client.post(reverse('payment_page'), {'plan': 'Bronze'})
        
        self.assertEqual(response.status_code, 302)  # Redirects after payment
        self.assertTrue(Payment.objects.filter(user=self.user, status='completed').exists())
        subscription = Subscription.objects.get(user=self.user)
        self.assertEqual(subscription.rate_plan, self.rate_plan)
        self.assertTrue(subscription.active)

    @patch('vm_management.views.send_smtp_email')
    def test_subscription_page(self, mock_send_email):
        """
        Test that the subscription page works correctly.
        Should update the user's subscription with the selected rate plan and activate it.
        """
        mock_send_email.return_value = None
        response = self.client.post(reverse('subscription_page'), {'plan': 'Bronze'})
        
        self.assertEqual(response.status_code, 302)  # Redirects after subscription
        subscription = Subscription.objects.get(user=self.user)
        self.assertEqual(subscription.rate_plan, self.rate_plan)
        self.assertTrue(subscription.active)

    def test_manage_users(self):
        # Ensure user is a parent to manage other users
        """
        Test that the manage_users view works correctly.
        Should assign the parent account to the managed user and activate their subscription.
        """
        self.user.subscription.is_parent = True
        self.user.subscription.save()
        child_user = User.objects.create_user(username='childuser', password='12345')
        
        response = self.client.post(reverse('manage_users'), {'child_username': 'childuser'})
        
        self.assertEqual(response.status_code, 302)  # Redirects after managing users
        child_subscription = Subscription.objects.get(user=child_user)
        self.assertEqual(child_subscription.parent_account, self.user)
        self.assertTrue(child_subscription.active)

    def test_get_user_payments(self):
        """
        Test that the get_user_payments view works correctly.
        Should return a list of the user's payments, with their status.
        """
        Payment.objects.create(user=self.user, amount=100, status='completed')
        response = self.client.get(reverse('user_payments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'completed')
