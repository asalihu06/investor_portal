from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from investors.models import InvestorProfile


class InvestmentTier(models.Model):
    name = models.CharField(max_length=100)
    minimum_assets = models.PositiveIntegerField()
    maximum_assets = models.PositiveIntegerField()
    minimum_investment = models.DecimalField(max_digits=15, decimal_places=2)
    return_rate = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_multiplier(self):
        multipliers = {
            'STANDARD': 1,
            'PREMIUM': 3,
        }
        return multipliers.get(self.name.upper(), 1)

    def __str__(self):
        return self.name


class Investment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('awaiting_payment', 'Awaiting Payment'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    FREQUENCY_CHOICES = (
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )

    investor = models.ForeignKey(
        InvestorProfile,
        on_delete=models.CASCADE,
        related_name='investments'
    )
    tier = models.ForeignKey(
        InvestmentTier,
        on_delete=models.PROTECT
    )
    number_of_assets = models.PositiveIntegerField(default=0)
    investment_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    payout_frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default='monthly'
    )
    duration_months = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    service_charge = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    management_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    asset_type = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def annual_roi(self):
        rate = Decimal(str(self.tier.return_rate)) / Decimal('100')
        return round(self.investment_amount * rate, 2)

    def weekly_return(self):
        return round(self.annual_roi() / Decimal('52'), 2)

    def monthly_return(self):
        return round(self.annual_roi() / Decimal('12'), 2)

    def expected_return(self):
        if self.payout_frequency == 'weekly':
            return self.weekly_return()
        return self.monthly_return()

    def total_roi(self):
        if not self.duration_months:
            return Decimal('0')
        if self.payout_frequency == 'weekly':
            periods = Decimal(str(self.duration_months)) * Decimal('4.33')
        else:
            periods = Decimal(str(self.duration_months))
        return round(self.expected_return() * periods, 2)

    def net_return(self):
        return self.investment_amount + self.total_roi()

    def asset_cost(self):
        total = self.allocations.aggregate(
            total=Sum('asset__purchase_value')
        )['total']
        return total or Decimal('0')

    def next_payment_date(self):
        if not self.start_date:
            return None
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        today = date.today()
        next_date = self.start_date
        if self.payout_frequency == 'weekly':
            while next_date <= today:
                next_date += timedelta(days=7)
        else:
            while next_date <= today:
                next_date += relativedelta(months=1)
        return next_date

    def total_paid_out(self):
        return self.payouts.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

    def is_expired(self):
        if not self.end_date:
            return False
        from datetime import date
        return date.today() >= self.end_date

    def days_remaining(self):
        if not self.end_date:
            return None
        from datetime import date
        delta = self.end_date - date.today()
        return max(delta.days, 0)

    def months_remaining(self):
        if not self.end_date or not self.start_date:
            return None
        from datetime import date
        today = date.today()
        if today >= self.end_date:
            return 0
        months = (self.end_date.year - today.year) * 12
        months += self.end_date.month - today.month
        return max(months, 0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.investor.user.username} - {self.tier.name}"