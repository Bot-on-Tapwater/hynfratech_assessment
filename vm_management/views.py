from datetime import datetime, timedelta
from django.utils import timezone
from functools import wraps
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import VM, ActionLog, Payment, Subscription, RatePlan, Backup
import subprocess

import logging

from django.core.mail import send_mail
from django.db import transaction

from accounts.models import CustomUser

from django.contrib import messages

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

import paramiko

from accounts.views import admin_or_standard_user_required, admin_required

from dotenv import load_dotenv, find_dotenv

# Load environment definition file
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger(__name__)

host_username = os.environ.get('HOST_USER')
host_home = os.environ.get('HOST_HOME')
host_password = os.environ.get('HOST_PASSWORD')
home_dir = os.getenv('HOST_HOME', '/root')  # Default to '/root' if HOME is not set
host_ip = os.getenv('HOST_IP')

def services_pricing(request):
    return render(request, "vm_management/services_clean.html")

def subscription_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            subscription = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            return redirect('services')

        if not subscription.active:
            return redirect('user_payments')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def run_vboxmanage_command(host, username, password, command):
    print(f"HOST: {host}, USERNAME: {username}, PASSWORD: {password}, COMMAND: {command}")
    print(f"HOST: {os.getenv('HOST_IP')}, USERNAME: {os.getenv('HOST_USER')}, PASSWORD: {os.getenv('PASSWORD')},")
    # port = 2112
    port = os.getenv('HOST_PORT')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect using the password
    ssh.connect(host, port, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()

    ssh.close()

    # Check if there is an actual error
    # if error and "progress" not in output.lower():
    #     raise Exception(f"Error executing command: {error}")
    
    return output

def send_smtp_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_HOST_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(settings.EMAIL_HOST_USER, to_email, msg.as_string())
    except Exception as e:
        print(f"An error occurred while sending email: {e}")

@admin_or_standard_user_required
def vm_list(request):
    # Fetch all VMs belonging to the logged-in user
    user_vms = VM.objects.filter(user=request.user)

    # Pass the VMs to the template
    return render(request, 'vm_management/vm_list_clean.html', {'vms': user_vms})

@admin_or_standard_user_required
@subscription_required
def create_vm(request):
    user = request.user
    subscription = Subscription.objects.get(user=user)

    # Determine which user should have their limits applied (for multi-client accounts)
    if subscription.parent_account:
        parent_account = subscription.parent_account
        # Assuming parent_account has a related name 'managed_users' pointing to CustomUser
        # Get users managed by the parent account (which are CustomUser objects)
        managed_users = CustomUser.objects.filter(subscription__parent_account=parent_account)
        user_vms_count = VM.objects.filter(user__in=managed_users).count()
        plan_limit = parent_account.subscription.rate_plan.max_vms
    else:
        parent_account = None
        user_vms_count = VM.objects.filter(user=user).count()
        plan_limit = subscription.rate_plan.max_vms

    # Check if user has reached their VM creation limit
    if user_vms_count >= plan_limit:
        messages.error(request, f"You've reached your VM creation limit of {plan_limit} VMs.")
        return redirect('vm_list')

    # VM creation logic
    if request.method == 'POST':
        name = request.POST.get('name')
        disk_size = int(request.POST.get('disk_size'))
        cpu = int(request.POST.get('cpu', 1))
        memory = int(request.POST.get('memory', 256))

        # Calculate price based on disk size
        price_per_mb = 0.01  # Example price per MB
        extra_mb = max(disk_size - 1024, 0)
        price = extra_mb * price_per_mb

        # Create a payment entry with status pending
        Payment.objects.create(
            user=user,
            amount=price,
            status='pending'
        )

        if not host_username or not host_ip or not host_password:
            raise ValueError("Environment variables for host connection are not set.")

        create_vm_cmd = f'vboxmanage createvm --name {name} --register'
        modify_vm_cmd = f'vboxmanage modifyvm {name} --memory {memory} --cpus {cpu} --vram 16 --nic1 nat'
        create_hd_cmd = f'vboxmanage createhd --filename ~/VirtualBox\\ VMs/{name}/{name}.vdi --size {disk_size}'

        run_vboxmanage_command(host_ip, host_username, host_password, create_vm_cmd)
        run_vboxmanage_command(host_ip, host_username, host_password, modify_vm_cmd)
        run_vboxmanage_command(host_ip, host_username, host_password, create_hd_cmd)

        # Save VM in database
        vm = VM.objects.create(name=name, user=user, disk_size=disk_size, status='stopped', cpu=cpu, memory=memory, price=price)
        ActionLog.objects.create(action_type='create', vm=vm, user=user)

        return redirect('vm_list')

    return render(request, 'vm_management/create_vm_clean.html')

@admin_or_standard_user_required
@subscription_required
def configure_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    if not host_username or not host_password:
        raise ValueError("HOST_USER or HOST_PASSWORD environment variables are not set.")

    # Check the VM status
    show_vm_info_cmd = f'vboxmanage showvminfo {vm.name} --machinereadable'
    vm_status_output = run_vboxmanage_command(host_ip, host_username, host_password, show_vm_info_cmd)

    if "VMState=\"running\"" in vm_status_output:
        # If VM is running, stop it before making modifications
        stop_vm_cmd = f'vboxmanage controlvm {vm.name} poweroff'
        run_vboxmanage_command(host_ip, host_username, host_password, stop_vm_cmd)

    if request.method == 'POST':
        # Get the configuration data from the form
        new_memory = request.POST.get('memory')
        new_cpu = request.POST.get('cpus')

        # Modify the VM configuration with the new values
        modify_vm_cmd = f'vboxmanage modifyvm {vm.name} --memory {new_memory} --cpus {new_cpu}'
        run_vboxmanage_command(host_ip, host_username, host_password, modify_vm_cmd)

        # Update the VM model
        logger.debug(f"Before saving: {vm.to_dict()}")
        vm.memory = int(new_memory)
        vm.cpu = int(new_cpu)
        try:
            vm.save()
            logger.debug(f"After saving: {vm.to_dict()}")
        except Exception as e:
            logger.error(f"Error saving VM: {e}", exc_info=True)

        ActionLog.objects.create(action_type='configure', vm=vm, user=request.user)

        return redirect('vm_list')

    return render(request, 'vm_management/configure_vm_clean.html', {'vm': vm})

@admin_or_standard_user_required
@subscription_required
def delete_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    if not host_username or not host_password:
        raise ValueError("HOST_USER or HOST_PASSWORD environment variables are not set.")

    # Use vboxmanage to delete VM
    unregister_vm_cmd = f'vboxmanage unregistervm {vm.name} --delete'
    run_vboxmanage_command(host_ip, host_username, host_password, unregister_vm_cmd)

    ActionLog.objects.create(action_type='delete', vm=vm, user=request.user)
    vm.delete()

    return redirect('vm_list')

@subscription_required
def backup_vm(request, vm_id):
    try:
        vm = VM.objects.get(id=vm_id)
        user = vm.user
        subscription = Subscription.objects.get(user=user)
    except VM.DoesNotExist:
        messages.error(request, "VM does not exist.")
        return redirect('vm_list')

    # Determine which user should have their limits applied (for multi-client accounts)
    if subscription.parent_account:
        parent_account = subscription.parent_account
        # Assuming parent_account has a related name 'managed_users' pointing to CustomUser
        # Count backups for the parent account and all managed users
        managed_users = CustomUser.objects.filter(subscription__parent_account=parent_account)
        user_backups_count = Backup.objects.filter(user__in=managed_users).count()
        plan_limit = parent_account.subscription.rate_plan.max_backups
    else:
        parent_account = None
        # Count backups for the current user
        user_backups_count = Backup.objects.filter(user=user).count()
        plan_limit = subscription.rate_plan.max_backups

    # Check if user has reached their backup creation limit
    if user_backups_count >= plan_limit:
        messages.error(request, f"You've reached your backup creation limit of {plan_limit} backups.")
        return redirect('vm_list')

    if not host_username or not host_ip or not host_password:
        raise ValueError("HOST_USER, HOST_IP, or HOST_PASSWORD environment variables are not set.")

    # Use vboxmanage to take a snapshot (backup)
    snapshot_cmd = f'vboxmanage snapshot {vm.name} take --name backup'
    run_vboxmanage_command(host_ip, host_username, host_password, snapshot_cmd)

    # Create a Backup record in the database
    Backup.objects.create(vm=vm, user=request.user)

    # Log the action
    ActionLog.objects.create(action_type='backup', vm=vm, user=request.user)

    messages.success(request, "Backup created successfully.")
    return redirect('vm_list')

@admin_or_standard_user_required
@subscription_required
def start_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    if not host_username or not host_password:
        raise ValueError("HOST_USER or HOST_PASSWORD environment variables are not set.")

    if vm.user == request.user:  # Ensure user owns the VM
        start_vm_cmd = f'vboxmanage startvm {vm.name} --type headless'
        run_vboxmanage_command(host_ip, host_username, host_password, start_vm_cmd)

        vm.status = 'running'
        vm.save()

        ActionLog.objects.create(action_type='start', vm=vm, user=request.user)
    
    return redirect('vm_list')

@admin_or_standard_user_required
@subscription_required
def stop_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    if not host_username or not host_password:
        raise ValueError("HOST_USER or HOST_PASSWORD environment variables are not set.")

    if vm.user == request.user:  # Ensure user owns the VM
        stop_vm_cmd = f'vboxmanage controlvm {vm.name} acpipowerbutton'
        run_vboxmanage_command(host_ip, host_username, host_password, stop_vm_cmd)

        vm.status = 'stopped'
        vm.save()

        ActionLog.objects.create(action_type='stop', vm=vm, user=request.user)
    
    return redirect('vm_list')

@admin_or_standard_user_required
@subscription_required
def vm_details(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    if not host_username or not host_password:
        raise ValueError("HOST_USER or HOST_PASSWORD environment variables are not set.")

    if vm.user == request.user:  # Ensure user owns the VM
        vm_info_cmd = f'vboxmanage showvminfo {vm.name}'
        vm_info_output = run_vboxmanage_command(host_ip, host_username, host_password, vm_info_cmd)
        
         # Process vm_info_output into a dictionary
        vm_details_dict = {}
        for line in vm_info_output.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)  # Split by the first colon
                vm_details_dict[key.strip()] = value.strip()  # Clean up spaces

        return render(request, 'vm_management/vm_details_clean.html', {'vm': vm, 'vm_details': vm_details_dict})
    
    return redirect('vm_list')

def transfer_vm(vm_id, new_user_id, original_user):
    try:
        with transaction.atomic():
            # Get the VM and the new user
            vm = VM.objects.get(id=vm_id)
            new_user = CustomUser.objects.get(id=new_user_id)

            # Update the VM's user
            vm.user = new_user
            vm.save()

            # Log the action
            ActionLog.objects.create(
                action_type='transfer',
                vm=vm,
                user=original_user
            )

            # Notify both users
            send_smtp_email(
                'VM Transfer Notification',
                f'The VM "{vm.name}" has been transferred to {new_user.username}.',
                new_user.email
            )
            send_smtp_email(
                'VM Transfer Notification',
                f'You have transferred the VM "{vm.name}" to {new_user.username}.',
                original_user.email
            )
    except VM.DoesNotExist:
        print(f"VM with id {vm_id} does not exist.")
    except CustomUser.DoesNotExist:
        print(f"User with id {new_user_id} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

@admin_required
def transfer_vm_view(request, vm_id):
    if request.method == 'POST':
        new_user_id = request.POST.get('new_user_id')

        # Validate the new user ID
        if not CustomUser.objects.filter(id=new_user_id).exists():
            messages.error(request, 'Invalid user selected.')
            return redirect('vm_list')

        # Call the transfer function
        transfer_vm(vm_id, new_user_id, request.user)
        messages.success(request, 'VM transferred successfully.')
        return redirect('vm_list')

    vm = VM.objects.get(id=vm_id)
    users = CustomUser.objects.exclude(id=vm.user.id)  # Exclude the current owner
    return render(request, 'vm_management/transfer_vm_clean.html', {'vm': vm, 'users': users})

@login_required
@admin_or_standard_user_required
def payment_page(request):
    rate_plans = RatePlan.objects.all()

    if request.method == 'POST':
        # amount = request.POST.get('amount')
        selected_plan_name = request.POST.get('plan')

        try:
            rate_plan = RatePlan.objects.get(name=selected_plan_name)
            amount = rate_plan.price
        except RatePlan.DoesNotExist:
            messages.error(request, "Invalid rate plan selected.")
            return redirect('payment_page')

        # Create a mock payment and mark it as completed
        payment = Payment.objects.create(user=request.user, amount=amount, status='completed')

        # Activate or update user's subscription
        subscription, created = Subscription.objects.get_or_create(user=request.user)
        subscription.active = True
        subscription.rate_plan = rate_plan  # Assign the selected rate plan
        subscription.start_date = datetime.now()
        subscription.end_date = datetime.now() + timedelta(days=30)  # Example: 1-month subscription
        subscription.save()

        messages.success(request, f"Payment successful! {rate_plan.name.capitalize()} Plan activated.")
        return redirect('vm_list')

    return render(request, 'vm_management/payment_page.html', {'rate_plans': rate_plans})

@admin_required
def get_all_payments(request):
    # Get all payment records
    payments = Payment.objects.all()

    # Pass the payment records to the template or as JSON
    context = {
        'payments': payments
    }
    return render(request, 'vm_management/admin_payments.html', context)

@login_required
def get_user_payments(request):
    # Get the logged-in user's payment records
    user_payments = Payment.objects.filter(user=request.user)

    # Pass the user's payment records to the template or as JSON
    context = {
        'user_payments': user_payments
    }
    return render(request, 'vm_management/user_payments_clean.html', context)

@login_required
def subscription_page(request):
    rate_plans = RatePlan.objects.all()

    if request.method == 'POST':
        selected_plan = request.POST.get('plan')
        rate_plan = RatePlan.objects.get(name=selected_plan)
        
        subscription, created = Subscription.objects.get_or_create(user=request.user)
        subscription.rate_plan = rate_plan
        subscription.active = True
        subscription.start_date = datetime.now()
        subscription.end_date = datetime.now() + timedelta(days=30)  # Example: 1-month subscription
        subscription.save()

        messages.success(request, f"Subscription updated to {rate_plan.name.capitalize()} Plan.")
        return redirect('subscription_page')

    return render(request, 'vm_management/subscription_page.html', {'rate_plans': rate_plans})

@admin_or_standard_user_required
@subscription_required
def manage_users(request):
    if not request.user.subscription.is_parent:
        messages.error(request, "You do not have permission to manage other users.")
        return redirect('subscription_page')
    
    user_subscription = Subscription.objects.filter(user=request.user).first()

    # List users managed by this account
    managed_users = Subscription.objects.filter(parent_account=request.user)

    users = CustomUser.objects.exclude(id=request.user.id)  # Exclude the current owner

    if request.method == 'POST':
        child_user = CustomUser.objects.get(username=request.POST.get('child_username'))
        child_subscription, created = Subscription.objects.get_or_create(user=child_user)
        child_subscription.parent_account = request.user
        child_subscription.active = True
        child_subscription.save()

        messages.success(request, f"{child_user.username} added to your account.")
        return redirect('manage_users')

    return render(request, 'vm_management/manage_users_clean.html', {'managed_users': managed_users, 'user_subscription': user_subscription, 'users':users},)

@admin_or_standard_user_required
def remove_user(request, user_id):
    if not request.user.subscription.is_parent:
        messages.error(request, "You do not have permission to manage other users.")
        return redirect('subscription_page')

    # Retrieve the user to be removed
    subscription = get_object_or_404(Subscription, user_id=user_id, parent_account=request.user)

    # Remove the user
    subscription.delete()

    messages.success(request, "User removed successfully.")
    return redirect('manage_users')

@admin_required
def get_logs(request):
    # Retrieve all action logs
    logs = ActionLog.objects.all().order_by('-timestamp')

    logs_dicts = [log.to_dict() for log in logs]

    # Render the logs to the template
    return render(request, 'vm_management/get_logs_clean.html', {'logs': logs_dicts})

@admin_required
def deactivate_subscription(request, user_id):
    # Get the user object or return 404 if not found
    user = get_object_or_404(CustomUser, id=user_id)

    # Try to get the user's subscription, if it exists
    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        # If no subscription exists, do nothing and return a message
        # return HttpResponse(f"{user.username} does not have a subscription.", status=404)
        return render(request, 'accounts/access_denied.html', {'error': f"{user.username} does not have a subscription."})

    # Set the subscription to inactive if it exists
    subscription.active = False
    subscription.end_date = timezone.now()  # Optionally set end date to now
    subscription.save()

    previous_url = request.META.get('HTTP_REFERER', '/')

    return redirect(previous_url)

    # return render(request, 'vm_management/all_users_details_clean.html')

@admin_required
def activate_subscription(request, user_id):
    # Get the user object or return 404 if not found
    user = get_object_or_404(CustomUser, id=user_id)

    # Try to get the user's subscription, if it exists
    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        # If no subscription exists, do nothing and return a message
        return render(request, 'accounts/access_denied.html', {'error': f"{user.username} does not have a subscription."})

    # Set the subscription to active if it exists
    subscription.active = True
    subscription.end_date = None  # Optionally clear the end date
    subscription.start_date = timezone.now()  # Set start date to now if activating
    subscription.save()

    previous_url = request.META.get('HTTP_REFERER', '/')

    return redirect(previous_url)

    # return render(request, 'vm_management/all_users_details_clean.html')

@admin_required
def user_details(request, user_id):
    # Get the user object or 404 if not found
    user = get_object_or_404(CustomUser, id=user_id)

    # Get all payments for this user
    payments = Payment.objects.filter(user=user)

    # Check if there are any overdue payments
    has_overdue_payments = any(payment.is_overdue() for payment in payments)

    # Prepare the data to pass to the template
    context = {
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'has_overdue_payments': has_overdue_payments,
    }

    return render(request, 'vm_management/user_details.html', context)

@admin_required
def all_users_details(request):
    # Get all users
    users = CustomUser.objects.all()

    # Prepare a list to hold user details
    user_details_list = []

    for user in users:
        # Get all payments for each user
        payments = Payment.objects.filter(user=user)

        # Check if the user has any overdue payments
        has_overdue_payments = any(payment.is_overdue() for payment in payments)

        # Get the subscription for the user
        subscription = Subscription.objects.filter(user=user).first()
        is_active = subscription.active if subscription else False

        # Prepare the user's details
        user_details = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'has_overdue_payments': has_overdue_payments,
            'is_active': is_active,
        }

        # Add the user's details to the list
        user_details_list.append(user_details)

    # Pass the list of user details to the template
    context = {
        'user_details_list': user_details_list
    }

    return render(request, 'vm_management/all_users_details_clean.html', context)


@admin_or_standard_user_required
def change_rate_plan(request, plan):
    # Get the currently logged-in user
    user = request.user

    # Get the rate plan by name
    try:
        new_rate_plan = RatePlan.objects.get(name=plan)
    except RatePlan.DoesNotExist:
        return HttpResponse(f"Rate plan '{plan}' does not exist.", status=404)
    
    # Get or create the user's subscription
    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        # return HttpResponse(f"You do not have a subscription.", status=404)
        return render(request, 'accounts/access_denied.html', {'error': f"You do not have a subscription."})
    
    # Update the subscription's rate plan
    subscription.rate_plan = new_rate_plan
    subscription.save()

    previous_url = request.META.get('HTTP_REFERER', '/')

    return redirect(previous_url)
    
    # return HttpResponse(f"Rate plan for {user.username} has been updated to {new_rate_plan.name}.")

@admin_or_standard_user_required
def mark_payments_completed(request, payment_id):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=403)
    
    # Get the specific pending payment for the logged-in user
    payment = get_object_or_404(Payment, id=payment_id, user=request.user, status='pending')

    # Mark the payment as completed
    payment.status = 'completed'
    payment.save()

    previous_url = request.META.get('HTTP_REFERER', '/')

    return redirect(previous_url)

    # return JsonResponse({"message": f"Payment {payment_id} marked as completed."})