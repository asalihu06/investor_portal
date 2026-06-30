from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import admin_required, investor_required
from .forms import RegisterForm


def login_choice_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/login_choice.html')


def admin_login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'admin':
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin account.')
    return render(request, 'accounts/login_admin.html')


def investor_login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'investor':
            login(request, user)
            return redirect('investor_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an investor account.')
    return render(request, 'accounts/login_investor.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                from investors.models import InvestorProfile
                InvestorProfile.objects.get_or_create(
                    user=user,
                    defaults={'phone_number': ''}
                )
                login(request, user)
                messages.success(request, 'Account created successfully.')
                return redirect('investor_dashboard')
            except Exception:
                form.add_error('email', 'An account with this email already exists.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login_choice')


@login_required
def dashboard_view(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    return redirect('investor_dashboard')

@investor_required
def investor_dashboard_view(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    try:
        profile = request.user.investorprofile
    except Exception:
        return redirect('profile_create')

    investments = profile.investments.all().order_by('-created_at')
    active_investments = investments.filter(status='active')

    from decimal import Decimal
    from django.db.models import Sum

    total_invested = investments.exclude(status='cancelled').aggregate(
        total=Sum('investment_amount')
    )['total'] or Decimal('0')

    total_paid_out = Decimal('0')
    for inv in active_investments:
        total_paid_out += inv.total_paid_out()

    weekly_investments = active_investments.filter(payout_frequency='weekly')
    monthly_investments = active_investments.filter(payout_frequency='monthly')

    total_weekly_return = sum(
        inv.weekly_return() for inv in weekly_investments
    ) or Decimal('0')

    total_monthly_return = sum(
        inv.monthly_return() for inv in monthly_investments
    ) or Decimal('0')

    next_payments = [
        inv.next_payment_date() for inv in active_investments
        if inv.next_payment_date()
    ]
    next_payment = min(next_payments) if next_payments else None

    context = {
        'profile': profile,
        'investments': investments,
        'active_investments': active_investments,
        'total_invested': total_invested,
        'total_paid_out': total_paid_out,
        'total_weekly_return': total_weekly_return,
        'total_monthly_return': total_monthly_return,
        'next_payment': next_payment,
    }
    return render(request, 'accounts/investor_dashboard.html', context)

@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        return redirect('investor_dashboard')

    from decimal import Decimal
    from django.db.models import Sum
    from investors.models import InvestorProfile
    from investments.models import Investment
    from transactions.models import Transaction

    total_investment_amount = Investment.objects.exclude(status='cancelled').aggregate(
        total=Sum('investment_amount')
    )['total'] or Decimal('0')

    context = {
        'total_investors': InvestorProfile.objects.count(),
        'total_investments': total_investment_amount,
        'pending_kyc': InvestorProfile.objects.filter(kyc_verified=False).count(),
        'active_investments': Investment.objects.filter(status='active').count(),
        'recent_investments': Investment.objects.order_by('-created_at')[:5],
        'recent_transactions': Transaction.objects.order_by('-created_at')[:5],
    }
    return render(request, 'accounts/admin_dashboard.html', context)