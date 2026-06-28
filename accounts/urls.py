from django.urls import path
from . import views

urlpatterns = [
    
    path('login/', views.login_choice_view, name='login_choice'),
    path('login/admin/', views.admin_login_view, name='admin_login'),
    path('login/investor/', views.investor_login_view, name='investor_login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/investor/', views.investor_dashboard_view, name='investor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
]