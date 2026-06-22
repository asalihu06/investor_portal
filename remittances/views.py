from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from accounts.decorators import admin_required
from investments.models import Investment
from assets.models import AssetAllocation
from .models import Remittance
from datetime import date


def get_expected_amount(allocation, investment):
    weekly = allocation.asset.weekly_return or Decimal('0')
    if investment.payout_frequency == 'monthly':
        return weekly * Decimal('4')
    return weekly


@admin_required
def central_payment_view(request):
    from investments.models import Investment

    active_investments = Investment.objects.filter(
        status='active'
    ).select_related('investor__user', 'tier')

    ready_for_payout = []
    pending_payments = []

    for investment in active_investments:
        allocations = investment.allocations.all()
        total_allocations = allocations.count()

        if total_allocations == 0:
            continue

        paid_allocations = allocations.filter(current_period_paid=True).count()

        if paid_allocations == total_allocations:
            ready_for_payout.append(investment)
        else:
            pending_payments.append({
                'investment': investment,
                'paid': paid_allocations,
                'total': total_allocations,
                'allocations': allocations,
            })

    return render(request, 'remittances/central_payment.html', {
        'ready_for_payout': ready_for_payout,
        'pending_payments': pending_payments,
    })


@admin_required
def log_asset_payment_view(request, allocation_pk):
    allocation = get_object_or_404(AssetAllocation, pk=allocation_pk)
    investment = allocation.investment

    if investment.status != 'active':
        messages.error(request, 'Investment is not active.')
        return redirect('central_payment')

    if request.method == 'POST':
        hirer_name = request.POST.get('hirer_name', allocation.hirer_name or 'Hirer')
        amount_received = request.POST.get('amount_received')
        notes = request.POST.get('notes', '')
        today = date.today()

        received = Decimal(str(amount_received))
        expected = get_expected_amount(allocation, investment)

        if received >= expected:
            status = 'received'
        elif received > 0:
            status = 'partial'
        else:
            status = 'missed'

        Remittance.objects.create(
            investment=investment,
            allocation=allocation,
            hirer_name=hirer_name,
            amount_received=received,
            expected_amount=expected,
            received_date=today,
            status=status,
            notes=notes,
            recorded_by=request.user,
        )

        if status == 'received':
            allocation.current_period_paid = True
            allocation.last_payment_date = today
            allocation.hirer_name = hirer_name
            allocation.save()
            messages.success(request, f'Payment logged for {allocation.asset.name}.')
        else:
            messages.warning(request, f'Partial/missed payment logged for {allocation.asset.name}.')

        return redirect('central_payment')

    expected = get_expected_amount(allocation, investment)

    return render(request, 'remittances/log_asset_payment.html', {
        'allocation': allocation,
        'investment': investment,
        'expected': expected,
    })


@admin_required
def issue_payment_view(request, investment_pk):
    investment = get_object_or_404(Investment, pk=investment_pk)

    if investment.status != 'active':
        messages.error(request, 'Investment is not active.')
        return redirect('central_payment')

    allocations = investment.allocations.all()
    if not all(a.current_period_paid for a in allocations):
        messages.error(request, 'Not all assets have been paid for this period.')
        return redirect('central_payment')

    if request.method == 'POST':
        from payouts.models import Payout
        from transactions.models import Transaction
        from auditlogs.models import AuditLog

        expected_amount = investment.expected_return()
        today = date.today()

        Payout.objects.create(
            investment=investment,
            amount=expected_amount,
            status='paid',
            payout_date=today,
        )

        Transaction.objects.create(
            investment=investment,
            transaction_type='return',
            amount=expected_amount,
            status='confirmed',
            reference=f"RET-{investment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        )

        allocations.update(current_period_paid=False)

        investment.remittances.filter(
            payout_generated=False
        ).update(payout_generated=True)

        AuditLog.objects.create(
            user=request.user,
            action='Payment Issued',
            model_name='Investment',
            object_id=investment.id,
            details=f"₦{expected_amount:,.2f} issued to {investment.investor.user.username}."
        )

        messages.success(
            request,
            f'₦{expected_amount:,.2f} payment issued to {investment.investor.user.username}.'
        )

    return redirect('central_payment')


@admin_required
def remittance_list_view(request):
    remittances = Remittance.objects.select_related(
        'investment__investor__user', 'recorded_by', 'allocation__asset'
    ).order_by('-received_date')
    return render(request, 'remittances/remittance_list.html', {
        'remittances': remittances
    })