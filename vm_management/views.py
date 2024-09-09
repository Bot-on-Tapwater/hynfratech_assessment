from datetime import datetime, timedelta, timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import VM, ActionLog, Payment, Subscription, RatePlan
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

logger = logging.getLogger(__name__)

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

def calculate_price(disk_size):
    price_per_mb = 0.01  # Example price per MB
    return disk_size * price_per_mb

@login_required
def vm_list(request):
    # Fetch all VMs belonging to the logged-in user
    user_vms = VM.objects.filter(user=request.user)

    # Pass the VMs to the template
    return render(request, 'vm_management/vm_list.html', {'vms': user_vms})

@login_required
def create_vm(request):
    user = request.user
    # Check subscription and VM limits
    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        messages.error(request, "You don't have an active subscription.")
        return redirect('subscription_page')

    # Check if the subscription is inactive
    if not subscription.active:
        messages.error(request, "Your subscription is inactive. Please make a payment to create more VMs.")
        return redirect('payment_page')

    # Determine which user should have their limits applied (for multi-client accounts)
    if subscription.parent_account:
        parent_account = subscription.parent_account
        user_vms_count = VM.objects.filter(user__in=parent_account.managed_users.all()).count()
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
        memory = int(request.POST.get('memory', 1024))

        # VM creation commands (VirtualBox in this case)
        subprocess.run([
            'vboxmanage', 'createvm', '--name', name, '--register'
        ])
        subprocess.run([
            'vboxmanage', 'modifyvm', name, '--memory', str(memory), '--cpus', str(cpu), '--vram', '16', '--nic1', 'nat'
        ])
        subprocess.run([
            'vboxmanage', 'createhd', '--filename', f'~/VirtualBox VMs/{name}/{name}.vdi', '--size', str(disk_size)
        ])

        # Save VM in database
        vm = VM.objects.create(name=name, user=request.user, disk_size=disk_size, status='stopped', cpu=cpu, memory=memory)
        ActionLog.objects.create(action_type='create', vm=vm, user=request.user)

        return redirect('vm_list')

    return render(request, 'vm_management/create_vm.html')


@login_required
def configure_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    # Check the VM status
    vm_status_output = subprocess.run(
        ['vboxmanage', 'showvminfo', vm.name, '--machinereadable'], 
        capture_output=True, text=True
    )

    if "VMState=\"running\"" in vm_status_output.stdout:
        # If VM is running, stop it before making modifications
        subprocess.run(['vboxmanage', 'controlvm', vm.name, 'poweroff'])

    if request.method == 'POST':
        # Get the configuration data from the form
        new_memory = request.POST.get('memory')
        new_cpu = request.POST.get('cpus')

        # Modify the VM configuration with the new values
        subprocess.run([
            'vboxmanage', 'modifyvm', vm.name, '--memory', new_memory, '--cpus', new_cpu
        ])

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

    return render(request, 'vm_management/configure_vm.html', {'vm': vm})



@login_required
def delete_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)

    ActionLog.objects.create(action_type='delete', vm=vm, user=request.user)
    
    # Use vboxmanage to delete VM
    subprocess.run(['vboxmanage', 'unregistervm', vm.name, '--delete'])

    vm.delete()    

    return redirect('vm_list')

@login_required
def backup_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)
    subprocess.run(['vboxmanage', 'snapshot', vm.name, 'take', 'backup'])
    ActionLog.objects.create(action_type='backup', vm=vm, user=request.user)
    return redirect('vm_list')

@login_required
def start_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)
    if vm.user == request.user:  # Ensure user owns the VM
        subprocess.run(['vboxmanage', 'startvm', vm.name, '--type', 'headless'])
        vm.status = 'running'
        vm.save()
        ActionLog.objects.create(action_type='start', vm=vm, user=request.user)
    return redirect('vm_list')

@login_required
def stop_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)
    if vm.user == request.user:  # Ensure user owns the VM
        subprocess.run(['vboxmanage', 'controlvm', vm.name, 'acpipowerbutton'])
        vm.status = 'stopped'
        vm.save()
        ActionLog.objects.create(action_type='stop', vm=vm, user=request.user)
    return redirect('vm_list')

@login_required
def restart_vm(request, vm_id):
    vm = VM.objects.get(id=vm_id)
    if vm.user == request.user:  # Ensure user owns the VM
        subprocess.run(['vboxmanage', 'controlvm', vm.name, 'reset'])
        ActionLog.objects.create(action_type='restart', vm=vm, user=request.user)
    return redirect('vm_list')

@login_required
def vm_details(request, vm_id):
    vm = VM.objects.get(id=vm_id)
    if vm.user == request.user:  # Ensure user owns the VM
        vm_info = subprocess.run(['vboxmanage', 'showvminfo', vm.name], capture_output=True, text=True)
        vm_details = vm_info.stdout  # Raw VM info output, you can parse and format this as needed

        return render(request, 'vm_management/vm_details.html', {'vm': vm, 'vm_details': vm_details})
    return redirect('vm_list')

# @login_required
# def configure_vm(request, vm_id):
#     vm = VM.objects.get(id=vm_id)

#     # Check the VM status
#     vm_status_output = subprocess.run(
#         ['vboxmanage', 'showvminfo', vm.name, '--machinereadable'], 
#         capture_output=True, text=True
#     )

#     if "VMState=\"running\"" in vm_status_output.stdout:
#         # If VM is running, stop it before making modifications
#         subprocess.run(['vboxmanage', 'controlvm', vm.name, 'poweroff'])

#     if request.method == 'POST':
#         # Get the configuration data from the form
#         new_memory = request.POST.get('memory')
#         new_cpu = request.POST.get('cpus')

#         # Modify the VM configuration with the new values
#         subprocess.run([
#             'vboxmanage', 'modifyvm', vm.name, '--memory', new_memory, '--cpus', new_cpu
#         ])

#         ActionLog.objects.create(action_type='configure', vm=vm, user=request.user)

#         return redirect('vm_list')

#     return render(request, 'vm_management/configure_vm.html', {'vm': vm})


@login_required
def view_vm_console(request, vm_id):
    vm = VM.objects.get(id=vm_id)
    if vm.user == request.user:  # Ensure user owns the VM
        console_output = subprocess.run(['vboxmanage', 'controlvm', vm.name, 'screenshotpng', '/tmp/vm_console.png'])
        ActionLog.objects.create(action_type='view_console', vm=vm, user=request.user)

        # You can either return the console image or display it in your frontend
        return redirect('vm_list')  # You can enhance this to show the console image or more details
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

@login_required
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
    return render(request, 'vm_management/transfer_vm.html', {'vm': vm, 'users': users})

@login_required
def payment_page(request):
    rate_plans = RatePlan.objects.all()

    if request.method == 'POST':
        amount = request.POST.get('amount')
        selected_plan_name = request.POST.get('plan')

        try:
            rate_plan = RatePlan.objects.get(name=selected_plan_name)
        except RatePlan.DoesNotExist:
            messages.error(request, "Invalid rate plan selected.")
            return redirect('payment_page')

        # Create a mock payment and mark it as completed
        payment = Payment.objects.create(user=request.user, amount=amount, status='completed')

        # Activate or update user's subscription
        subscription, created = Subscription.objects.get_or_create(user=request.user)
        subscription.active = True
        subscription.rate_plan = rate_plan  # Assign the selected rate plan
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=30)  # Example: 1-month subscription
        subscription.save()

        messages.success(request, f"Payment successful! {rate_plan.name.capitalize()} Plan activated.")
        return redirect('vm_list')

    return render(request, 'vm_management/payment_page.html', {'rate_plans': rate_plans})

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

@login_required
def manage_users(request):
    if not request.user.subscription.is_parent:
        messages.error(request, "You do not have permission to manage other users.")
        return redirect('subscription_page')

    # List users managed by this account
    managed_users = Subscription.objects.filter(parent_account=request.user)

    if request.method == 'POST':
        child_user = CustomUser.objects.get(username=request.POST.get('child_username'))
        child_subscription, created = Subscription.objects.get_or_create(user=child_user)
        child_subscription.parent_account = request.user
        child_subscription.active = True
        child_subscription.save()

        messages.success(request, f"{child_user.username} added to your account.")
        return redirect('manage_users')

    return render(request, 'vm_management/manage_users.html', {'managed_users': managed_users})
