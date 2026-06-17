from decimal import Decimal
from django.utils import timezone
from .models import Investment
from transactions.models import Transaction
from payouts.models import Payout
from auditlogs.models import AuditLog


def activate_investment(investment, activated_by, duration_months=None, roi_rate=None):
    if investment.status not in ['pending', 'awaiting_payment']:
        raise ValueError("Only pending or awaiting payment investments can be activated.")

    from datetime import date
    from dateutil.relativedelta import relativedelta

    allocations = investment.allocations.select_related('asset')
    if not allocations.exists():
        raise ValueError("Cannot activate investment with no allocated assets.")

    service_charge = sum(a.asset.service_charge for a in allocations)
    management_fee = sum(a.asset.management_fee for a in allocations)
    asset_cost = sum(a.asset.purchase_value for a in allocations)
    total_amount = sum(a.asset.total_cost() for a in allocations)

    investment.status = 'active'
    investment.start_date = date.today()
    investment.service_charge = Decimal(str(service_charge))
    investment.management_fee = Decimal(str(management_fee))
    investment.investment_amount = Decimal(str(total_amount))

    if roi_rate:
        investment.roi_rate = Decimal(str(roi_rate))

    if duration_months:
        investment.duration_months = duration_months
        investment.end_date = date.today() + relativedelta(months=duration_months)

    investment.save()

    Transaction.objects.create(
        investment=investment,
        transaction_type='deposit',
        amount=investment.investment_amount,
        status='confirmed',
        reference=f"DEP-{investment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    AuditLog.objects.create(
        user=activated_by,
        action='Investment Activated',
        model_name='Investment',
        object_id=investment.id,
        details=f"Investment {investment.id} activated. Duration: {duration_months} months. ROI rate: {roi_rate}%. Asset cost: {asset_cost}. Service charge: {service_charge}. Management fee: {management_fee}. Total: {total_amount}."
    )


def calculate_return(investment):
    rate = Decimal(str(investment.tier.return_rate)) / Decimal('100')
    return investment.investment_amount * rate



def generate_payout(investment, generated_by):
    if investment.status != 'active':
        raise ValueError("Payouts can only be generated for active investments.")
    return_amount = investment.expected_return()

    payout = Payout.objects.create(
        investment=investment,
        amount=return_amount,
        status='pending',
        payout_date=timezone.now().date()
    )

    Transaction.objects.create(
        investment=investment,
        transaction_type='return',
        amount=return_amount,
        status='confirmed',
        reference=f"RET-{investment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    AuditLog.objects.create(
        user=generated_by,
        action='Payout Generated',
        model_name='Payout',
        object_id=payout.id,
        details=f"{investment.payout_frequency.capitalize()} payout of {return_amount} generated for investment {investment.id} — {investment.investor.user.username}"
    )

    return payout

def complete_investment(investment, completed_by):
    if investment.status != 'active':
        raise ValueError("Only active investments can be completed.")

    investment.status = 'completed'
    investment.save()

    investment.payouts.filter(status='pending').update(status='paid')

    Transaction.objects.create(
        investment=investment,
        transaction_type='payout',
        amount=investment.investment_amount,
        status='confirmed',
        reference=f"CPLT-{investment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    AuditLog.objects.create(
        user=completed_by,
        action='Investment Completed',
        model_name='Investment',
        object_id=investment.id,
        details=f"Investment {investment.id} completed for {investment.investor.user.username}"
    )


def cancel_investment(investment, cancelled_by):
    if investment.status not in ['pending', 'awaiting_payment', 'active']:
        raise ValueError("Only pending, awaiting payment, or active investments can be cancelled.")

    investment.status = 'cancelled'
    investment.save()

    AuditLog.objects.create(
        user=cancelled_by,
        action='Investment Cancelled',
        model_name='Investment',
        object_id=investment.id,
        details=f"Investment {investment.id} cancelled for {investment.investor.user.username}"
    )