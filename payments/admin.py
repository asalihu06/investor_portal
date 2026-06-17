from django.contrib import admin
from .models import PaymentRecord

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('reference', 'investment', 'amount', 'status', 'created_at', 'paid_at')
    list_filter = ('status',)
    search_fields = ('reference', 'investment__investor__user__username')
    readonly_fields = ('reference', 'amount', 'paystack_response', 'created_at', 'paid_at')