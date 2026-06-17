from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    list_filter = ('model_name',)
    search_fields = ('user__username', 'action', 'model_name')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'timestamp', 'details')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False