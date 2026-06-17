from django.db import models
from django.conf import settings


class InvestorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    phone_number = models.CharField(max_length=20, blank=True, default='')
    bank_name = models.CharField(max_length=100, blank=True, default='')
    account_number = models.CharField(max_length=20, blank=True, default='')
    account_name = models.CharField(max_length=200, blank=True, default='')
    kyc_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username