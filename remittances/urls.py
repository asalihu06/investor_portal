from django.urls import path
from . import views

urlpatterns = [
    path('', views.central_payment_view, name='central_payment'),
    path('history/', views.remittance_list_view, name='remittance_list'),
    path('log/<int:allocation_pk>/', views.log_asset_payment_view, name='log_asset_payment'),
    path('issue/<int:investment_pk>/', views.issue_payment_view, name='issue_payment'),
    path('issue-all/', views.issue_all_payments_view, name='issue_all_payments'),
    path('confirm/<int:allocation_pk>/', views.confirm_payment_view, name='confirm_payment'),
    path('hirer/<int:allocation_pk>/edit/', views.edit_hirer_view, name='edit_hirer'),
    path('webhook/paystack', views.paystack_webhook_view, name='paystack_hirer_webhook'),
    path('confirm-all/', views.confirm_all_payments_view, name='confirm_all_payments'),
]