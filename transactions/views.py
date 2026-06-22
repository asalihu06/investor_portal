from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction
from investors.models import InvestorProfile
from accounts.decorators import admin_required, investor_required


@investor_required
def transaction_list_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    
    transactions = Transaction.objects.filter(
        investment__investor=profile
    ).order_by('-created_at')
    return render(request, 'transactions/transaction_list.html', {
        'transactions': transactions
    })

@investor_required
def transaction_detail_view(request, pk):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    transaction = get_object_or_404(
        Transaction, pk=pk, investment__investor=profile
    )

    paystack_reference = None
    if transaction.transaction_type == 'deposit':
        try:
            paystack_reference = transaction.investment.payment.reference
        except Exception:
            pass

    return render(request, 'transactions/transaction_detail.html', {
        'transaction': transaction,
        'paystack_reference': paystack_reference,
    })


@admin_required
def admin_transaction_list_view(request):
    transactions = Transaction.objects.select_related(
        'investment__investor__user', 'investment__tier'
    ).order_by('-created_at')
    return render(request, 'transactions/admin/transaction_list.html', {
        'transactions': transactions
    })