from django.urls import path
from . import views

urlpatterns = [
    path('pay/<int:investment_pk>/', views.initiate_payment_view, name='initiate_payment'),
    path('verify/<str:reference>/', views.payment_verify_view, name='payment_verify'),
    path('webhook/', views.paystack_webhook_view, name='paystack_webhook'),
]