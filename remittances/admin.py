from django.contrib import admin
from .models import Remittance

@admin.register(Remittance)
class RemittanceAdmin(admin.ModelAdmin):
    list_display = ('investment', 'hirer_name', 'amount_received', 'expected_amount', 'status', 'received_date', 'payout_generated')
    list_filter = ('status', 'payout_generated')
    readonly_fields = ('created_at',)