from django.contrib import admin
from .models import InvestorProfile

@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'kyc_verified', 'created_at')
    list_filter = ('kyc_verified',)
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at',)