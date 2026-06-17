from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list_view, name='transaction_list'),
    path('<int:pk>/', views.transaction_detail_view, name='transaction_detail'),
    path('manage/', views.admin_transaction_list_view, name='admin_transaction_list'),
]