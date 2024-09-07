from django.db import models
from accounts.models import CustomUser  # Import the CustomUser model from accounts app

class VM(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('running', 'Running'), ('stopped', 'Stopped')])
    disk_size = models.IntegerField()  # Disk size in MB

    def __str__(self):
        return self.name

class ActionLog(models.Model):
    action_type = models.CharField(max_length=100)
    vm = models.ForeignKey(VM, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} on {self.vm.name} by {self.user.username}"
