from django import forms
from .models import Investment, InvestmentTier

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ('tier', 'number_of_assets', 'investment_amount')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tier'].queryset = InvestmentTier.objects.filter(active=True)