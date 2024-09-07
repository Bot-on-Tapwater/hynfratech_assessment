from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import VM, ActionLog
import subprocess

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
    if request.method == 'POST':
        name = request.POST.get('name')
        disk_size = int(request.POST.get('disk_size'))
        price = calculate_price(disk_size)

        # Use vboxmanage to create VM
        subprocess.run([
            'vboxmanage', 'createvm', '--name', name, '--register'
        ])
        subprocess.run([
            'vboxmanage', 'modifyvm', name, '--memory', '1024', '--cpus', '1', '--vram', '16', '--nic1', 'nat'
        ])
        subprocess.run([
            'vboxmanage', 'createhd', '--filename', f'~/VirtualBox VMs/{name}/{name}.vdi', '--size', str(disk_size)
        ])
        subprocess.run([
            'vboxmanage', 'storagectl', name, '--name', 'SATA Controller', '--add', 'sata', '--controller', 'IntelAHCI'
        ])
        subprocess.run([
            'vboxmanage', 'storageattach', name, '--storagectl', 'SATA Controller', '--port', '0', '--device', '0', '--type', 'hdd', '--medium', f'~/VirtualBox VMs/{name}/{name}.vdi'
        ])

        vm = VM.objects.create(name=name, user=request.user, disk_size=disk_size, status='stopped')

        ActionLog.objects.create(action_type='create', vm=vm, user=request.user)

        return redirect('vm_list')

    return render(request, 'vm_management/create_vm.html')

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
