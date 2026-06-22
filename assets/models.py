from django.db import models
from django.core.exceptions import ValidationError


class Asset(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('allocated', 'Allocated'),
        ('maintenance', 'Maintenance'),
        ('inactive', 'Inactive'),
    )

    name = models.CharField(max_length=200)
    asset_code = models.CharField(max_length=50, unique=True, blank=True)
    asset_type = models.CharField(max_length=100)
    purchase_value = models.DecimalField(max_digits=15, decimal_places=2)
    service_charge = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    management_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    weekly_return = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    duration_weeks = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_asset_code(self):
        prefix = ''.join(
            word[0].upper() for word in self.asset_type.split()
        )[:4]

        existing = Asset.objects.filter(
            asset_code__startswith=f"{prefix}-"
        ).exclude(pk=self.pk)

        max_num = 0
        for asset in existing:
            try:
                num = int(asset.asset_code.split('-')[-1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass

        return f"{prefix}-{str(max_num + 1).zfill(3)}"

    def save(self, *args, **kwargs):
        if not self.asset_code:
            self.asset_code = self.generate_asset_code()
        super().save(*args, **kwargs)

    def total_cost(self):
        return self.purchase_value + self.service_charge + self.management_fee

    def monthly_return_amount(self):
        if not self.weekly_return:
            return None
        from decimal import Decimal
        return self.weekly_return * Decimal('4')

    def total_expected_return(self):
        if not self.weekly_return or not self.duration_weeks:
            return None
        return self.weekly_return * self.duration_weeks

    def __str__(self):
        return f"{self.name} ({self.asset_code})"


class AssetAllocation(models.Model):
    investment = models.ForeignKey(
        'investments.Investment',
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    hirer_name = models.CharField(max_length=200, blank=True)
    hirer_phone = models.CharField(max_length=20, blank=True)
    allocated_at = models.DateTimeField(auto_now_add=True)

    # Payment tracking
    current_period_paid = models.BooleanField(default=False)
    last_payment_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('investment', 'asset')

    def unit_price(self):
        return (self.asset.purchase_value * self.investment.tier.get_multiplier()) + \
                self.asset.service_charge + self.asset.management_fee

    def total_price(self):
        return self.unit_price() * self.quantity

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.asset.status = 'allocated'
        self.asset.save()

    def __str__(self):
        return f"{self.asset.name} → Investment {self.investment.id}"