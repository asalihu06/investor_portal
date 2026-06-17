from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InvestorProfile
from .forms import InvestorProfileForm, BankDetailsForm
from accounts.decorators import admin_required, investor_required


@investor_required
def profile_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')
    return render(request, 'investors/profile.html', {'profile': profile})

@investor_required
def profile_create_view(request):
    try:
        request.user.investorprofile
        return redirect('profile')
    except InvestorProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        form = InvestorProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully.')
            return redirect('profile')
    else:
        form = InvestorProfileForm()
    return render(request, 'investors/profile_create.html', {'form': form})

@investor_required
def profile_edit_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    if request.method == 'POST':
        form = InvestorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = InvestorProfileForm(instance=profile)
    return render(request, 'investors/profile_edit.html', {'form': form})


@admin_required
def admin_investor_list_view(request):
    investors = InvestorProfile.objects.select_related('user').order_by('-created_at')
    return render(request, 'investors/admin/investor_list.html', {'investors': investors})

@admin_required
def admin_investor_detail_view(request, pk):
    investor = get_object_or_404(InvestorProfile, pk=pk)
    investments = investor.investments.all().order_by('-created_at')
    return render(request, 'investors/admin/investor_detail.html', {
        'investor': investor,
        'investments': investments,
    })

@admin_required
def admin_kyc_approve_view(request, pk):
    investor = get_object_or_404(InvestorProfile, pk=pk)
    investor.kyc_verified = True
    investor.save()
    from auditlogs.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action='KYC Approved',
        model_name='InvestorProfile',
        object_id=investor.id,
        details=f"KYC approved for {investor.user.username}"
    )
    messages.success(request, f'KYC approved for {investor.user.username}.')
    return redirect('admin_investor_detail', pk=pk)

@investor_required
def add_bank_details_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    if not profile.kyc_verified:
        messages.error(request, 'Bank details can only be added after KYC verification.')
        return redirect('profile')

    if request.method == 'POST':
        form = BankDetailsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank details saved successfully.')
            return redirect('profile')
    else:
        form = BankDetailsForm(instance=profile)
    return render(request, 'investors/add_bank_details.html', {'form': form})

@admin_required
def admin_kyc_revoke_view(request, pk):
    investor = get_object_or_404(InvestorProfile, pk=pk)
    investor.kyc_verified = False
    investor.save()
    from auditlogs.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action='KYC Revoked',
        model_name='InvestorProfile',
        object_id=investor.id,
        details=f"KYC revoked for {investor.user.username}"
    )
    messages.success(request, f'KYC revoked for {investor.user.username}.')
    return redirect('admin_investor_detail', pk=pk)