from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Payout
from investors.models import InvestorProfile
from accounts.decorators import admin_required, investor_required
from auditlogs.models import AuditLog


@investor_required
def payout_list_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    
    payouts = Payout.objects.filter(
        investment__investor=profile
    ).order_by('-created_at')
    return render(request, 'payouts/payout_list.html', {'payouts': payouts})

@investor_required
def payout_detail_view(request, pk):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    payout = get_object_or_404(
        Payout, pk=pk, investment__investor=profile
    )
    return render(request, 'payouts/payout_detail.html', {'payout': payout})

@admin_required
def admin_payout_list_view(request):
    payouts = Payout.objects.select_related(
        'investment__investor__user', 'investment__tier'
    ).order_by('-created_at')
    return render(request, 'payouts/admin/payout_list.html', {'payouts': payouts})

@admin_required
def admin_payout_mark_paid_view(request, pk):
    payout = get_object_or_404(Payout, pk=pk)
    payout.status = 'paid'
    payout.save()
    AuditLog.objects.create(
        user=request.user,
        action='Payout Marked Paid',
        model_name='Payout',
        object_id=payout.id,
        details=f"Payout {payout.id} marked as paid for {payout.investment.investor.user.username}"
    )
    messages.success(request, 'Payout marked as paid.')
    return redirect('admin_payout_list')