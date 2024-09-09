from django.db import models
from accounts.models import CustomUser  # Import the CustomUser model from accounts app

class VM(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('running', 'Running'), ('stopped', 'Stopped')])
    disk_size = models.IntegerField()  # Disk size in MB
    cpu = models.IntegerField(default=1)  # Default to 1 CPU
    memory = models.IntegerField(default=1024)  # Memory in MB, default to 1024 MB
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Price in currency

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Calculate the price before saving
        self.price = self.calculate_price(self.disk_size)
        super().save(*args, **kwargs)

    def calculate_price(self, disk_size):
        price_per_mb = 0.01  # Example price per MB
        return disk_size * price_per_mb

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
