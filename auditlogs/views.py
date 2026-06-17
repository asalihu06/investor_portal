from django.shortcuts import render
from .models import AuditLog
from investors.views import admin_required

@admin_required
def admin_auditlog_list_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'auditlogs/admin/auditlog_list.html', {'logs': logs})