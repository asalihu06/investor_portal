from django.contrib import admin
from .models import Asset, AssetAllocation

class AssetAllocationInline(admin.TabularInline):
    model = AssetAllocation
    extra = 0
    readonly_fields = ('allocated_at',)
    autocomplete_fields = ('asset',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_code', 'asset_type', 'purchase_value', 'status', 'created_at')
    list_filter = ('status', 'asset_type')
    search_fields = ('name', 'asset_code')
    readonly_fields = ('created_at',)

@admin.register(AssetAllocation)
class AssetAllocationAdmin(admin.ModelAdmin):
    list_display = ('asset', 'investment', 'allocated_at')
    search_fields = ('asset__name', 'investment__investor__user__username')
    readonly_fields = ('allocated_at',)