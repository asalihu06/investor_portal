from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/create/', views.profile_create_view, name='profile_create'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/bank/', views.add_bank_details_view, name='add_bank_details'),
    path('manage/', views.admin_investor_list_view, name='admin_investor_list'),
    path('manage/<int:pk>/', views.admin_investor_detail_view, name='admin_investor_detail'),
    path('manage/<int:pk>/kyc/approve/', views.admin_kyc_approve_view, name='admin_kyc_approve'),
    path('manage/<int:pk>/kyc/revoke/', views.admin_kyc_revoke_view, name='admin_kyc_revoke'),
]