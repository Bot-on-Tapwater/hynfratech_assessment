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
    
    # Subscription page to view/upgrade/downgrade plan
    path('subscription/', views.subscription_page, name='subscription_page'),

    # Manage child users
    path('manage-users/', views.manage_users, name='manage_users'),
]


