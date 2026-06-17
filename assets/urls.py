from django.urls import path
from . import views

urlpatterns = [
    path('', views.asset_list_view, name='asset_list'),
    path('<int:pk>/', views.asset_detail_view, name='asset_detail'),
    path('manage/', views.admin_asset_list_view, name='admin_asset_list'),
    path('manage/create/', views.admin_asset_create_view, name='admin_asset_create'),
    path('manage/<int:pk>/edit/', views.admin_asset_edit_view, name='admin_asset_edit'),
]