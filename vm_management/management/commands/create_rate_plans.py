# Create a management command: myapp/management/commands/create_rate_plans.py
from django.core.management.base import BaseCommand
from vm_management.models import RatePlan

class Command(BaseCommand):
    help = 'Create default rate plans'

    def handle(self, *args, **kwargs):
        RatePlan.create_plans()
        self.stdout.write(self.style.SUCCESS('Successfully created rate plans'))
