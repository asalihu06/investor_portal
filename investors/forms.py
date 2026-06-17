from django import forms
from .models import InvestorProfile


class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = ('phone_number',)


class BankDetailsForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = ('bank_name', 'account_number', 'account_name')

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if not account_number.isdigit():
            raise forms.ValidationError('Account number must contain digits only.')
        if len(account_number) != 10:
            raise forms.ValidationError('Account number must be exactly 10 digits.')
        return account_number