from django import forms
from .models import Investment, InvestmentTier

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ('tier', 'number_of_assets', 'investment_amount')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tier'].queryset = InvestmentTier.objects.filter(active=True)

from django import forms


class RemittanceForm(forms.Form):
    hirer_name = forms.CharField(max_length=200)
    expected_amount = forms.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    amount_received = forms.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    received_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))