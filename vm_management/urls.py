from django.urls import path
from . import views

urlpatterns = [
    path('', views.vm_list, name='vm_list'),
    path('create/', views.create_vm, name='create_vm'),
    path('delete/<int:vm_id>/', views.delete_vm, name='delete_vm'),
    path('backup/<int:vm_id>/', views.backup_vm, name='backup_vm'),
    path('start/<int:vm_id>/', views.start_vm, name='start_vm'),
    path('stop/<int:vm_id>/', views.stop_vm, name='stop_vm'),
    path('details/<int:vm_id>/', views.vm_details, name='vm_details'),
    path('configure/<int:vm_id>/', views.configure_vm, name='configure_vm'),
    path('transfer_vm/<int:vm_id>/', views.transfer_vm_view, name='transfer_vm'),
    path('payment/', views.payment_page, name='payment_page'),
    path('payments/admin/', views.get_all_payments, name='admin_payments'),
    path('payments/user/', views.get_user_payments, name='user_payments'),
    path('payments/complete/<int:payment_id>/', views.mark_payments_completed, name='mark_payments_completed'),
    
    # Subscription page to view/upgrade/downgrade plan
    path('subscription/', views.subscription_page, name='subscription_page'),
    path('change-rate-plan/<str:plan>/', views.change_rate_plan, name='change_rate_plan'),

    # Manage child users
    path('manage-users/', views.manage_users, name='manage_users'),
    path('remove-user/<int:user_id>/', views.remove_user, name='remove_user'),
    path('user/<int:user_id>/deactivate-subscription/', views.deactivate_subscription, name='deactivate_subscription'),
    path('user/<int:user_id>/activate_subscription/', views.activate_subscription, name='activate_subscription'),
    path('user/<int:user_id>/', views.user_details, name='user_details'),
    path('all-users/', views.all_users_details, name='all_users_details'),

    # Action logs
    path('logs/', views.get_logs, name='logs'),

    # Services page
    path('services/', views.services_pricing, name='services'),
]


