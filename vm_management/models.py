from datetime import timedelta
from django.db import models
from accounts.models import CustomUser  # Import the CustomUser model from accounts app
from datetime import datetime, timedelta
from django.utils import timezone
from django.forms.models import model_to_dict

class VM(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('running', 'Running'), ('stopped', 'Stopped')])
    disk_size = models.IntegerField(default=1024)  # Disk size in MB
    cpu = models.IntegerField(default=1)  # Default to 1 CPU
    memory = models.IntegerField(default=256)  # Memory in MB, default to 1024 MB
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Price in currency

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user': self.user.username,  # Assuming you want the username instead of the user ID
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'disk_size': self.disk_size,
            'cpu': self.cpu,
            'memory': self.memory,
            'price': self.price,
        }
    
class Backup(models.Model):
    vm = models.ForeignKey(VM, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)  # Optional field for description

    def __str__(self):
        return f"Backup for {self.vm.name} by {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def to_dict(self):
        return {
            'id': self.id,
            'vm': self.vm.to_dict(),
            'user': self.user.username,
            'created_at': self.created_at.isoformat(),
            'description': self.description,
        }

class ActionLog(models.Model):
    action_type = models.CharField(max_length=100)
    vm = models.ForeignKey(VM, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} on {self.vm.name} by {self.user.username}"

    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'vm': self.vm.to_dict(),  # Including VM details in the dictionary
            'user': self.user.username,  # Assuming you want the username instead of the user ID
            'timestamp': self.timestamp.isoformat(),
        }

class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.user.username} - {self.status}"

    def save(self, *args, **kwargs):
        # Only set the due_date if the status is 'pending' and it hasn't been set yet
        if self.status == 'pending' and self.due_date is None:
            if self.timestamp is None:
                self.timestamp = datetime.now()  # Set timestamp to now if it's not set
            self.due_date = self.timestamp + timedelta(days=30)
        super().save(*args, **kwargs)

    def is_overdue(self):
        # Check if the payment is overdue
        if self.status == 'pending' and self.due_date and timezone.now() > self.due_date:
            return True
        return False

    def is_in_good_standing(self):
        # Check if user has any overdue payments
        pending_payments = Payment.objects.filter(user=self.user, status='pending')
        for payment in pending_payments:
            if payment.is_overdue():
                return False
        return True

    def to_dict(self):
        # Convert the model fields to a dictionary
        payment_dict = model_to_dict(self)
        # Add the is_overdue field to the dictionary
        payment_dict['is_overdue'] = self.is_overdue()
        return payment_dict

class RatePlan(models.Model):
    PLAN_CHOICES = [
        ('platinum', 'Platinum'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('bronze', 'Bronze'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    max_vms = models.IntegerField()  # Maximum number of VMs allowed under this plan
    max_backups = models.IntegerField()  # Maximum number of backups allowed
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the plan

    def __str__(self):
        return f"{self.name.capitalize()} Plan"

    @classmethod
    def create_plans(cls):
        # Define the plans
        plans = [
            {'name': 'bronze', 'max_vms': 1, 'max_backups': 1, 'price': 100},
            {'name': 'silver', 'max_vms': 2, 'max_backups': 2, 'price': 200},
            {'name': 'gold', 'max_vms': 4, 'max_backups': 4, 'price': 400},
            {'name': 'platinum', 'max_vms': 8, 'max_backups': 8, 'price': 800},
        ]

        # Create the plans
        for plan in plans:
            cls.objects.get_or_create(**plan)

class Subscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    parent_account = models.ForeignKey(CustomUser, related_name='managed_users', on_delete=models.SET_NULL, null=True, blank=True)
    is_parent = models.BooleanField(default=True)  # Defines whether this account is a parent or child account

    def __str__(self):
        return f"Subscription for {self.user.username}: {self.rate_plan.name if self.rate_plan else 'No Plan'}"

    def can_create_vm(self):
        # Check if the user can create more VMs based on their plan
        user_vm_count = VM.objects.filter(user=self.user).count()
        return user_vm_count < self.rate_plan.max_vms

    def can_create_backup(self):
        # Check if the user can create more backups based on their plan
        user_backup_count = ActionLog.objects.filter(user=self.user, action_type='backup').count()
        return user_backup_count < self.rate_plan.max_backups

