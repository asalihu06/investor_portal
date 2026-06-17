from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_auditlog_list_view, name='admin_auditlog_list'),
]