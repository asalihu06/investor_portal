from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from accounts.decorators import admin_required
from investments.models import Investment
from assets.models import AssetAllocation
from .models import Remittance
from datetime import date
import json, hmac, hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


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
def issue_all_payments_view(request):
    if request.method != 'POST':
        return redirect('central_payment')

    from payouts.models import Payout
    from transactions.models import Transaction
    from auditlogs.models import AuditLog
    from decimal import Decimal

    active_investments = Investment.objects.filter(status='active')
    issued_count = 0
    total_issued = Decimal('0')

    for investment in active_investments:
        allocations = investment.allocations.all()
        total = allocations.count()
        if total == 0:
            continue
        all_paid = allocations.filter(current_period_paid=True).count() == total
        if not all_paid:
            continue

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
            details=f"₦{expected_amount:,.2f} issued to {investment.investor.user.username} via bulk issue."
        )

        issued_count += 1
        total_issued += expected_amount

    messages.success(
        request,
        f'{issued_count} payment(s) issued, totaling ₦{total_issued:,.2f}.'
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

@admin_required
def confirm_payment_view(request, allocation_pk):
    allocation = get_object_or_404(AssetAllocation, pk=allocation_pk)
    investment = allocation.investment

    if request.method != 'POST':
        return redirect('central_payment')

    if investment.status != 'active':
        messages.error(request, 'Investment is not active.')
        return redirect('central_payment')

    if allocation.current_period_paid:
        messages.warning(request, f'{allocation.asset.name} already confirmed for this cycle.')
        return redirect('central_payment')

    expected = get_expected_amount(allocation, investment)
    today = date.today()

    Remittance.objects.create(
        investment=investment,
        allocation=allocation,
        hirer_name=allocation.hirer_name or 'Hirer',
        amount_received=expected,
        expected_amount=expected,
        received_date=today,
        status='received',
        notes='',
        recorded_by=request.user,
    )

    allocation.current_period_paid = True
    allocation.last_payment_date = today
    allocation.save()

    messages.success(request, f'Payment confirmed for {allocation.asset.name}.')
    return redirect('central_payment')


@admin_required
def edit_hirer_view(request, allocation_pk):
    allocation = get_object_or_404(AssetAllocation, pk=allocation_pk)
    investment = allocation.investment

    if request.method == 'POST':
        allocation.hirer_name = request.POST.get('hirer_name', '').strip()
        allocation.hirer_phone = request.POST.get('hirer_phone', '').strip()
        allocation.save()
        messages.success(request, f'Hirer details updated for {allocation.asset.name}.')
        return redirect('manage_investment', pk=investment.pk)

    return render(request, 'remittances/edit_hirer.html', {
        'allocation': allocation,
        'investment': investment,
    })


@csrf_exempt
def paystack_webhook_view(request):
    if request.method != 'POST':
        return HttpResponse(status=405)


    paystack_secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    signature = request.headers.get('X-Paystack-Signature', '')
    computed = hmac.new(paystack_secret, request.body, hashlib.sha512).hexdigest()

    if signature != computed:
        return HttpResponse(status=401)

    payload = json.loads(request.body)
    event = payload.get('event')

    if event != 'charge.success':
        return HttpResponse(status=200)

    data = payload.get('data', {})
    metadata = data.get('metadata', {})
    allocation_pk = metadata.get('allocation_pk')

    if not allocation_pk:
        return HttpResponse(status=200)

    try:
        allocation = AssetAllocation.objects.get(pk=allocation_pk)
        investment = allocation.investment

        if investment.status != 'active':
            return HttpResponse(status=200)

        if allocation.current_period_paid:
            return HttpResponse(status=200)

        expected = get_expected_amount(allocation, investment)
        today = date.today()

        Remittance.objects.create(
            investment=investment,
            allocation=allocation,
            hirer_name=allocation.hirer_name or 'Hirer',
            amount_received=expected,
            expected_amount=expected,
            received_date=today,
            status='received',
            notes='Auto-confirmed via Paystack',
            recorded_by=None,
        )

        allocation.current_period_paid = True
        allocation.last_payment_date = today
        allocation.save()

    except AssetAllocation.DoesNotExist:
        pass

    return HttpResponse(status=200)