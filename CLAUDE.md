# Enigma Transport Investor Portal — Project Guide

## Project Overview
Asset-backed hire purchase investment platform for Nigerian market.
Investors fund transport assets (vehicles), earn weekly/monthly returns from hire purchase remittances.

## Tech Stack
- Python 3.14.2
- Django 6.0.6
- Tailwind CSS (CDN)
- SQLite (development) → PostgreSQL (production)
- Paystack (investor payments only)

## Project Structure
investor_portal/
├── accounts/       → User auth, login, register, dashboards
├── assets/         → Transport assets management
├── auditlogs/      → Platform activity logs
├── config/         → Settings, URLs
├── investments/    → Investment creation, management, services
├── investors/      → Investor profiles, KYC, bank details
├── payments/       → Paystack integration
├── payouts/        → Return payouts to investors
├── transactions/   → All financial transactions
├── templates/      → All HTML templates
└── manage.py

## Key Design Rules
- SVG icons only — no emojis in templates
- Monetary figures: `{% load humanize %}` with `|floatformat:2|intcomma`
- Button sizing: `text-sm`, `py-3` consistently
- Files created manually in VS Code (UTF-8 encoding — PowerShell causes null bytes)
- SVG icons use `stroke="currentColor"` not hardcoded hex
- No `text-lg`, `py-4` on buttons

## Color System (Tailwind config in base.html)
- `primary` → #1a6b2f (dark green)
- `primary-light` → #22c55e (bright green)
- `primary-dark` → #14532d (darker green)

## User Roles
- `admin` → Custom admin panel at `/accounts/dashboard/admin/`
- `investor` → Investor portal at `/accounts/dashboard/investor/`
- Login choice page at `/accounts/login/`
- Admin login at `/accounts/login/admin/`
- Investor login at `/accounts/login/investor/`

## Investment Flow
Step 1: Select Tier (/investments/create/)
Step 2: Select Assets (/investments/select-assets/)
Step 3: Review & Pay (/investments/review/)
Step 4: Paystack Payment (/payments/pay/<id>/)
Step 5: Verify & Activate (/payments/verify/<ref>/)
Step 6: Investment Active → Assets Auto-Allocated


## Money Flow
- Investor → Enigma: Paystack popup (test keys: sk_test_..., pk_test_...)
- Enigma → Investor: Manual bank transfer (admin marks payout as paid)
- Hirer → Enigma: Outside the portal (cash/bank remittance)

## Asset Model
Each asset has:
- `purchase_value` → What Enigma paid
- `service_charge` → One-time charge added to investor cost
- `management_fee` → Management fee added to investor cost
- `total_cost()` → purchase_value + service_charge + management_fee

## Investment Model
Key fields:
- `investment_amount` → Total paid by investor (sum of asset total_costs)
- `service_charge` → Total service charges from all assets
- `management_fee` → Total management fees from all assets
- `payout_frequency` → weekly or monthly
- `duration_months` → Set by admin on activation
- `start_date` / `end_date` → Set on activation
- `status` → pending → active → completed/cancelled

## KYC
- Currently manual — admin toggles `kyc_verified` on InvestorProfile
- Bank details locked until KYC approved
- Dojah/Prembly API integration deferred to later

## Payout Process
1. Admin generates payout → `Payout` record created, `Transaction` record created
2. Admin physically transfers to investor bank account
3. Admin marks payout as paid in portal
4. Investor sees updated Total Paid Out on dashboard

## Admin Panel URLs
- Dashboard: `/accounts/dashboard/admin/`
- Investors: `/investors/manage/`
- Investments: `/investments/manage/`
- Assets: `/assets/manage/`
- Transactions: `/transactions/manage/`
- Payouts: `/payouts/manage/`
- Audit Logs: `/auditlogs/`

## Services (investments/services.py)
- `activate_investment(investment, activated_by, duration_months, service_charge, management_fee)`
- `generate_payout(investment, generated_by)`
- `complete_investment(investment, completed_by)`
- `cancel_investment(investment, cancelled_by)`

## Sessions Used
- `selected_tier_id` → Tier chosen in step 1
- `selected_asset_ids` → Assets chosen in step 2
- `selected_frequency` → Weekly/monthly chosen in step 1
- `pending_investment_id` → Investment created in step 3
- `pending_asset_ids` → Assets to allocate after payment

## Common Issues & Fixes
- **Null bytes in files** → Use Python to write files, not PowerShell echo
- **Circular imports** → Use string references e.g. `'investments.Investment'`
- **Pylance Django errors** → Select venv interpreter in VS Code (Ctrl+Shift+P)
- **Duplicate Paystack reference** → Delete old pending PaymentRecord before creating new
- **Session lost after payment** → Store asset IDs in session before payment initiation

## Installed Apps
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'accounts',
    'assets',
    'auditlogs',
    'investments',
    'investors',
    'payments',
    'payouts',
    'transactions',
]
```

## Environment Variables (move to .env before production)
```python
PAYSTACK_SECRET_KEY = 'sk_test_...'
PAYSTACK_PUBLIC_KEY = 'pk_test_...'
SECRET_KEY = 'django-...'
DEBUG = True  # Set to False in production
```

## Production Checklist
- [ ] Switch SQLite → PostgreSQL
- [ ] Set DEBUG = False
- [ ] Move secrets to environment variables
- [ ] Configure static files (whitenoise or S3)
- [ ] Switch Paystack test keys → live keys
- [ ] Set ALLOWED_HOSTS
- [ ] Configure email backend (Gmail SMTP or SendGrid)
- [ ] Integrate KYC API (Prembly or Smile Identity)
- [ ] Remove CLAUDE.md