from django.urls import path
from . import views

urlpatterns = [
    path('', views.vm_list, name='vm_list'),
    path('create/', views.create_vm, name='create_vm'),
    path('delete/<int:vm_id>/', views.delete_vm, name='delete_vm'),
    path('backup/<int:vm_id>/', views.backup_vm, name='backup_vm'),
]
