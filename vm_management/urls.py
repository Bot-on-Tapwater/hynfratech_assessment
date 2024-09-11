from django.urls import path
from . import views

urlpatterns = [
    path('', views.vm_list, name='vm_list'),
    path('create/', views.create_vm, name='create_vm'),
    path('delete/<int:vm_id>/', views.delete_vm, name='delete_vm'),
    path('backup/<int:vm_id>/', views.backup_vm, name='backup_vm'),
    path('start/<int:vm_id>/', views.start_vm, name='start_vm'),
    path('stop/<int:vm_id>/', views.stop_vm, name='stop_vm'),
    path('restart/<int:vm_id>/', views.restart_vm, name='restart_vm'),
    path('details/<int:vm_id>/', views.vm_details, name='vm_details'),
    path('configure/<int:vm_id>/', views.configure_vm, name='configure_vm'),
    # path('console/<int:vm_id>/', views.view_vm_console, name='view_vm_console'),
    path('transfer_vm/<int:vm_id>/', views.transfer_vm_view, name='transfer_vm'),
    path('payment/', views.payment_page, name='payment_page'),
    # Subscription page to view/upgrade/downgrade plan
    path('subscription/', views.subscription_page, name='subscription_page'),

    # Manage child users
    path('manage-users/', views.manage_users, name='manage_users'),
]


