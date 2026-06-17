from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('investment', 'transaction_type', 'amount', 'status', 'reference', 'created_at')
    list_filter = ('transaction_type', 'status')
    search_fields = ('reference', 'investment__investor__user__username')
    readonly_fields = ('created_at',)