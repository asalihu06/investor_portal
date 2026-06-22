from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Asset, AssetAllocation
from .forms import AssetAllocationForm, AssetForm
from investments.models import Investment
from investors.models import InvestorProfile
from accounts.decorators import admin_required, investor_required


@investor_required
def asset_list_view(request):
    try:
        profile = request.user.investorprofile
    except InvestorProfile.DoesNotExist:
        return redirect('profile_create')

    allocations = AssetAllocation.objects.filter(
        investment__investor=profile
    ).select_related('asset', 'investment__tier').order_by('-allocated_at')

    return render(request, 'assets/asset_list.html', {'allocations': allocations})


@investor_required
def asset_detail_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'assets/asset_detail.html', {'asset': asset})


@admin_required
def admin_asset_list_view(request):
    assets = Asset.objects.all().order_by('-created_at')
    return render(request, 'assets/admin/asset_list.html', {'assets': assets})


@admin_required
def admin_asset_create_view(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset created successfully.')
            return redirect('admin_asset_list')
    else:
        form = AssetForm()
    return render(request, 'assets/admin/asset_create.html', {'form': form})


@admin_required
def admin_asset_edit_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset updated successfully.')
            return redirect('admin_asset_list')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'assets/admin/asset_edit.html', {
        'form': form, 'asset': asset
    })

@admin_required
def admin_asset_delete_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if asset.status == 'allocated':
        messages.error(request, f'Cannot delete {asset.name}  it is currently allocated to an investment.')
        return redirect('admin_asset_list')

    if request.method == 'POST':
        name = asset.name
        asset.delete()
        messages.success(request, f'{name} deleted successfully.')
        return redirect('admin_asset_list')

    return redirect('admin_asset_list')