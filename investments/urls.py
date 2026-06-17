from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.admin_investment_list_view, name='admin_investment_list'),
    path('', views.investment_list_view, name='investment_list'),
    path('create/', views.investment_create_view, name='investment_create'),
    path('select-assets/', views.select_assets_view, name='select_assets'),
    path('review/', views.investment_review_view, name='investment_review'),
    path('<int:pk>/', views.investment_detail_view, name='investment_detail'),
    path('<int:pk>/manage/', views.manage_investment_view, name='manage_investment'),
    path('<int:pk>/activate/', views.activate_investment_view, name='activate_investment'),
    path('<int:pk>/payout/', views.generate_payout_view, name='generate_payout'),
    path('<int:pk>/complete/', views.complete_investment_view, name='complete_investment'),
    path('<int:pk>/cancel/', views.cancel_investment_view, name='cancel_investment'),
    path('admin/investments/<int:pk>/assign-assets/', views.admin_assign_assets_view, name='admin_assign_assets'),
]