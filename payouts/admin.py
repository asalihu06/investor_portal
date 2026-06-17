from django.contrib import admin
from .models import Payout

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('investment', 'amount', 'status', 'payout_date', 'created_at')
    list_filter = ('status',)
    search_fields = ('investment__investor__user__username',)
    readonly_fields = ('created_at',)