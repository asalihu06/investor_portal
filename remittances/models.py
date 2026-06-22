from django.db import models
from django.conf import settings


class Remittance(models.Model):
    STATUS_CHOICES = (
        ('received', 'Received'),
        ('partial', 'Partial'),
        ('missed', 'Missed'),
    )

    investment = models.ForeignKey(
        'investments.Investment',
        on_delete=models.CASCADE,
        related_name='remittances'
    )
    allocation = models.ForeignKey(
        'assets.AssetAllocation',
        on_delete=models.CASCADE,
        related_name='remittances',
        null=True, blank=True
    )
    hirer_name = models.CharField(max_length=200)
    amount_received = models.DecimalField(max_digits=15, decimal_places=2)
    expected_amount = models.DecimalField(max_digits=15, decimal_places=2)
    received_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    payout_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"₦{self.amount_received} from {self.hirer_name} on {self.received_date}"