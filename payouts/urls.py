from django.urls import path
from . import views

urlpatterns = [
    path('', views.payout_list_view, name='payout_list'),
    path('<int:pk>/', views.payout_detail_view, name='payout_detail'),
    path('manage/', views.admin_payout_list_view, name='admin_payout_list'),
    path('manage/<int:pk>/paid/', views.admin_payout_mark_paid_view, name='admin_payout_mark_paid'),
]