from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from .models import Investment, InvestmentTier
from investors.models import InvestorProfile
from accounts.decorators import admin_required, investor_required
from .services import activate_investment, generate_payout, complete_investment, cancel_investment
from assets.models import Asset, AssetAllocation


@investor_required
def investment_list_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')
    investments = profile.investments.all().order_by('-created_at')
    return render(request, 'investments/investment_list.html', {'investments': investments})


@investor_required
def investment_create_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    if not profile.kyc_verified:
        messages.error(request, 'Your account must be KYC verified before you can make an investment.')
        return redirect('investor_dashboard')

    tiers = InvestmentTier.objects.filter(active=True)

    if request.method == 'POST':
        tier_id = request.POST.get('tier')
        tier = get_object_or_404(InvestmentTier, pk=tier_id, active=True)
        asset_count = int(request.POST.get('asset_count', tier.minimum_assets))
        asset_count = max(tier.minimum_assets, min(asset_count, tier.maximum_assets))
        request.session['selected_tier_id'] = tier.id
        request.session['selected_frequency'] = request.POST.get('frequency', 'monthly')
        request.session['selected_asset_count'] = asset_count
        return redirect('select_assets')

    return render(request, 'investments/investment_create.html', {'tiers': tiers})


@investor_required
def select_assets_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    tier_id = request.session.get('selected_tier_id')
    if not tier_id:
        return redirect('investment_create')

    tier = get_object_or_404(InvestmentTier, pk=tier_id)

    from django.db.models import Min
    asset_types = Asset.objects.filter(
        status='available'
    ).values('asset_type').annotate(
        sample_id=Min('id')
    ).distinct()

    asset_type_list = []
    for at in asset_types:
        sample = Asset.objects.get(id=at['sample_id'])
        multiplier = tier.get_multiplier()
        unit_price = (sample.purchase_value * multiplier) + sample.service_charge + sample.management_fee
        weekly = round(unit_price * (Decimal(str(tier.return_rate)) / Decimal('100')) / Decimal('52'), 2)
        monthly = round(unit_price * (Decimal(str(tier.return_rate)) / Decimal('100')) / Decimal('12'), 2)
        asset_type_list.append({
            'asset_type': at['asset_type'],
            'sample': sample,
            'unit_price': unit_price,
            'weekly_roi': weekly,
            'monthly_roi': monthly,
        })

    max_quantity = tier.maximum_assets

    if request.method == 'POST':
        selected_type = request.POST.get('asset_type')

        if not selected_type:
            messages.error(request, 'Please select an asset type.')
            return render(request, 'investments/select_assets.html', {
                'tier': tier,
                'asset_type_list': asset_type_list,
                'max_quantity': max_quantity,
            })

        # Quantity fixed by tier multiplier
        quantity = tier.get_multiplier()

        available_count = Asset.objects.filter(
            asset_type=selected_type,
            status='available'
        ).count()

        if available_count < quantity:
            messages.error(request, f'Only {available_count} unit(s) of {selected_type} available.')
            return render(request, 'investments/select_assets.html', {
                'tier': tier,
                'asset_type_list': asset_type_list,
                'max_quantity': max_quantity,
            })

        request.session['selected_asset_type'] = selected_type
        request.session['selected_quantity'] = quantity
        return redirect('investment_review')

    return render(request, 'investments/select_assets.html', {
        'tier': tier,
        'asset_type_list': asset_type_list,
        'max_quantity': max_quantity,
    })


@investor_required
def investment_review_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    tier_id = request.session.get('selected_tier_id')
    asset_type = request.session.get('selected_asset_type')
    quantity = request.session.get('selected_quantity', 1)
    frequency = request.session.get('selected_frequency', 'monthly')

    if not tier_id or not asset_type:
        return redirect('investment_list')

    tier = get_object_or_404(InvestmentTier, pk=tier_id)

    sample_asset = Asset.objects.filter(
        asset_type=asset_type, status='available'
    ).first()

    if not sample_asset:
        messages.error(request, 'No assets of this type available.')
        return redirect('select_assets')

    multiplier = tier.get_multiplier()
    unit_price = (sample_asset.purchase_value * multiplier) + sample_asset.service_charge + sample_asset.management_fee
    total_amount = unit_price * quantity
    asset_cost = sample_asset.purchase_value * multiplier * quantity
    total_service_charge = sample_asset.service_charge * quantity
    total_management_fee = sample_asset.management_fee * quantity

    annual_roi = total_amount * (Decimal(str(tier.return_rate)) / Decimal('100'))
    weekly = round(annual_roi / Decimal('52'), 2)
    monthly = round(annual_roi / Decimal('12'), 2)

    if request.method == 'POST':
        investment = Investment.objects.create(
            investor=profile,
            tier=tier,
            number_of_assets=quantity,
            asset_type=asset_type,
            quantity=quantity,
            investment_amount=total_amount,
            service_charge=total_service_charge,
            management_fee=total_management_fee,
            payout_frequency=frequency,
            status='pending',
        )

        request.session['pending_investment_id'] = investment.id
        request.session.pop('selected_tier_id', None)
        request.session.pop('selected_asset_type', None)
        request.session.pop('selected_quantity', None)
        request.session.pop('selected_frequency', None)

        return redirect('initiate_payment', investment_pk=investment.pk)

    return render(request, 'investments/investment_review.html', {
        'tier': tier,
        'asset_type': asset_type,
        'quantity': quantity,
        'sample_asset': sample_asset,
        'unit_price': unit_price,
        'total_amount': total_amount,
        'asset_cost': asset_cost,
        'total_service_charge': total_service_charge,
        'total_management_fee': total_management_fee,
        'weekly_return': weekly,
        'monthly_return': monthly,
        'frequency': frequency,
    })


@investor_required
def investment_detail_view(request, pk):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    investment = get_object_or_404(Investment, pk=pk, investor=profile)

    request.session.pop('selected_tier_id', None)
    request.session.pop('selected_asset_ids', None)
    request.session.pop('selected_frequency', None)
    request.session.pop('pending_investment_id', None)

    allocations = investment.allocations.all()
    transactions = investment.transactions.all().order_by('-created_at')
    payouts = investment.payouts.all().order_by('-created_at')

    return render(request, 'investments/investment_detail.html', {
        'investment': investment,
        'allocations': allocations,
        'transactions': transactions,
        'payouts': payouts,
    })


@admin_required
def admin_investment_list_view(request):
    investments = Investment.objects.select_related(
        'investor__user', 'tier'
    ).order_by('-created_at')
    return render(request, 'investments/admin/investment_list.html', {
        'investments': investments
    })


@admin_required
def manage_investment_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    allocations = investment.allocations.all()
    transactions = investment.transactions.all().order_by('-created_at')
    payouts = investment.payouts.all().order_by('-created_at')

    allocated_asset_ids = allocations.values_list('asset_id', flat=True)
    available_assets = Asset.objects.filter(status='available').exclude(id__in=allocated_asset_ids)

    return render(request, 'investments/manage_investment.html', {
        'investment': investment,
        'allocations': allocations,
        'transactions': transactions,
        'payouts': payouts,
        'available_assets': available_assets,
    })


@admin_required
def admin_assign_assets_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)

    if investment.status != 'pending':
        messages.error(request, 'Assets can only be assigned to pending investments.')
        return redirect('manage_investment', pk=pk)

    if request.method == 'POST':
        asset_ids = request.POST.getlist('asset_ids')

        if not asset_ids:
            messages.error(request, 'Please select at least one asset.')
            return redirect('manage_investment', pk=pk)

        total_after = investment.allocations.count() + len(asset_ids)
        if total_after > investment.number_of_assets:
            messages.error(request, f'This investment can only have {investment.number_of_assets} asset(s). Currently has {investment.allocations.count()}.')
            return redirect('manage_investment', pk=pk)

        assets = Asset.objects.filter(id__in=asset_ids, status='available')
        created = 0
        for asset in assets:
            AssetAllocation.objects.bulk_create([
                AssetAllocation(investment=investment, asset=asset)
            ])
            asset.status = 'allocated'
            asset.save()
            created += 1

        from auditlogs.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='Assets Assigned',
            model_name='Investment',
            object_id=investment.id,
            details=f"{created} asset(s) assigned to investment {investment.id}."
        )

        messages.success(request, f'{created} asset(s) assigned successfully.')

    return redirect('manage_investment', pk=pk)


@admin_required
def activate_investment_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    if request.method == 'POST':
        try:
            duration_months = int(request.POST.get('duration_months', 0))
            roi_rate = request.POST.get('roi_rate')
            activate_investment(
                investment,
                activated_by=request.user,
                duration_months=duration_months,
                roi_rate=roi_rate,
            )
            messages.success(request, f'Investment activated. ROI: {roi_rate}%.')
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('manage_investment', pk=pk)


@admin_required
def generate_payout_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    try:
        generate_payout(investment, generated_by=request.user)
        messages.success(request, 'Payout generated successfully.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('manage_investment', pk=pk)


@admin_required
def complete_investment_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    try:
        complete_investment(investment, completed_by=request.user)
        messages.success(request, 'Investment marked as completed.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('manage_investment', pk=pk)


@admin_required
def cancel_investment_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    try:
        cancel_investment(investment, cancelled_by=request.user)
        messages.success(request, 'Investment cancelled.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('manage_investment', pk=pk)


@admin_required
def set_charges_view(request, pk):
    investment = get_object_or_404(Investment, pk=pk)

    if investment.status != 'pending':
        messages.error(request, 'Charges can only be set on pending investments.')
        return redirect('manage_investment', pk=pk)

    if request.method == 'POST':
        service_charge = Decimal(request.POST.get('service_charge', '0'))
        management_fee = Decimal(request.POST.get('management_fee', '0'))

        investment.service_charge = service_charge
        investment.management_fee = management_fee
        investment.investment_amount = investment.investment_amount + service_charge + management_fee
        investment.status = 'awaiting_payment'
        investment.save()

        from auditlogs.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='Charges Set',
            model_name='Investment',
            object_id=investment.id,
            details=f"Service charge: {service_charge}, Management fee: {management_fee}."
        )

        messages.success(request, 'Charges set. Investor can now proceed to payment.')
        return redirect('manage_investment', pk=pk)

    return render(request, 'investments/set_charges.html', {'investment': investment})