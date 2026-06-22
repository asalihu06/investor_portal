from django import forms
from .models import Asset, AssetAllocation


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = (
            'name', 'asset_type',
            'purchase_value',
            'service_charge', 'management_fee',
            'weekly_return', 'duration_weeks',
            'status'
        )


class AssetAllocationForm(forms.ModelForm):
    class Meta:
        model = AssetAllocation
        fields = ('asset',)

    def __init__(self, *args, investment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.investment = investment
        self.fields['asset'].queryset = Asset.objects.filter(status='available')

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get('asset')
        if self.investment:
            current_count = self.investment.allocations.count()
            if current_count >= self.investment.number_of_assets:
                raise forms.ValidationError(
                    f'This investment can only have {self.investment.number_of_assets} assets.'
                )
        return cleaned_data