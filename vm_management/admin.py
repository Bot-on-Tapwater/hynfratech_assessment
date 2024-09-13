from django.contrib import admin
from .models import VM, ActionLog, Payment, Subscription, RatePlan, Backup
from accounts.models import CustomUser  # Import CustomUser from accounts app

@admin.register(VM)
class VMAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'disk_size', 'cpu', 'memory', 'created_at')
    list_filter = ('status', 'user')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'vm', 'user', 'timestamp')
    list_filter = ('action_type', 'user')
    search_fields = ('action_type', 'vm__name', 'user__username')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'email')
    ordering = ('username',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'timestamp')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'rate_plan', 'active', 'start_date', 'end_date', 'is_parent', 'parent_account')

@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_vms', 'max_backups', 'price')

@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ('vm', 'user', 'created_at',)