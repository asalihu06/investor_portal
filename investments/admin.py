from django.contrib import admin
from .models import Investment, InvestmentTier

@admin.register(InvestmentTier)
class InvestmentTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'minimum_assets', 'maximum_assets', 'minimum_investment', 'return_rate', 'active')
    list_filter = ('active',)
    search_fields = ('name',)

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('investor', 'tier', 'investment_amount', 'number_of_assets', 'status', 'start_date', 'created_at')
    list_filter = ('status', 'tier')
    search_fields = ('investor__user__username',)
    readonly_fields = ('created_at',)