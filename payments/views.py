import hmac
import hashlib
import json
import uuid
import requests
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from investments.models import Investment
from investments.services import activate_investment
from accounts.decorators import investor_required
from .models import PaymentRecord


def generate_reference():
    return f"ENIGMA-{uuid.uuid4().hex[:12].upper()}"


@investor_required
def initiate_payment_view(request, investment_pk):
    try:
        profile = request.user.investorprofile
    except Exception:
        return redirect('profile_create')

    investment = get_object_or_404(
        Investment, pk=investment_pk, investor=profile
    )

    if hasattr(investment, 'payment') and investment.payment.status == 'success':
        messages.info(request, 'This investment has already been paid for.')
        return redirect('investment_detail', pk=investment_pk)

    if investment.status not in ['pending', 'awaiting_payment']:
        messages.error(request, 'This investment cannot be paid for.')
        return redirect('investment_detail', pk=investment_pk)

    from assets.models import AssetAllocation
    allocated_ids = list(
        AssetAllocation.objects.filter(
            investment=investment
        ).values_list('asset_id', flat=True)
    )

    asset_ids = request.session.get('selected_asset_ids', allocated_ids)
    request.session['pending_asset_ids'] = [str(i) for i in asset_ids]

    PaymentRecord.objects.filter(
        investment=investment,
        status__in=['pending', 'failed']
    ).delete()

    payment = PaymentRecord.objects.create(
        investment=investment,
        reference=generate_reference(),
        amount=investment.investment_amount,
        status='pending',
    )

    amount_kobo = int(investment.investment_amount * 100)

    context = {
        'investment': investment,
        'payment': payment,
        'amount_kobo': amount_kobo,
        'public_key': settings.PAYSTACK_PUBLIC_KEY,
        'email': request.user.email,
    }
    return render(request, 'payments/initiate_payment.html', context)


@investor_required
def payment_verify_view(request, reference):
    payment = get_object_or_404(PaymentRecord, reference=reference)

    if payment.status == 'success':
        messages.success(request, 'Payment confirmed. Please wait while admin activates your assets.')
        return redirect('investment_detail', pk=payment.investment.pk)

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            },
            timeout=30
        )

        data = response.json()

        if response.status_code == 200 and data['data']['status'] == 'success':
            payment.status = 'success'
            payment.paystack_response = data['data']
            payment.paid_at = timezone.now()
            payment.save()

            investment = payment.investment

            messages.success(request, 'Payment confirmed. Please wait while admin activates your assets.')
            return redirect('investment_detail', pk=investment.pk)

        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment failed: {data.get("message", "Unknown error")}')
            return redirect('investment_detail', pk=payment.investment.pk)

    except Exception as e:
        import traceback
        messages.error(request, f'Verification error: {traceback.format_exc()}')
        return redirect('investment_detail', pk=payment.investment.pk)

@csrf_exempt
def paystack_webhook_view(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    paystack_signature = request.headers.get('X-Paystack-Signature')
    if not paystack_signature:
        return HttpResponse(status=400)

    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        request.body,
        hashlib.sha512
    ).hexdigest()

    if computed != paystack_signature:
        return HttpResponse(status=401)

    payload = json.loads(request.body)
    event = payload.get('event')

    if event == 'charge.success':
        data = payload.get('data', {})
        reference = data.get('reference')

        try:
            payment = PaymentRecord.objects.get(reference=reference)
            if payment.status != 'success':
                payment.status = 'success'
                payment.paystack_response = data
                payment.paid_at = timezone.now()
                payment.save()

                from accounts.models import User
                system_user = User.objects.filter(role='admin').first()
                investment = payment.investment
                investment.refresh_from_db()

                if investment.status in ['pending', 'awaiting_payment']:
                    if investment.allocations.exists():
                        activate_investment(investment, activated_by=system_user)

        except PaymentRecord.DoesNotExist:
            pass

    return HttpResponse(status=200)