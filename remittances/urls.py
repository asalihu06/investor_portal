from django.urls import path
from . import views

urlpatterns = [
    path('', views.central_payment_view, name='central_payment'),
    path('history/', views.remittance_list_view, name='remittance_list'),
    path('log/<int:allocation_pk>/', views.log_asset_payment_view, name='log_asset_payment'),
    path('issue/<int:investment_pk>/', views.issue_payment_view, name='issue_payment'),
]