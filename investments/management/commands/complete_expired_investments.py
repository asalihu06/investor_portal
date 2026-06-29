from django.core.management.base import BaseCommand
from django.utils import timezone
from investments.models import Investment
from auditlogs.models import AuditLog


class Command(BaseCommand):
    help = 'Auto-complete investments that have reached their end date'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        expired = Investment.objects.filter(
            status='active',
            end_date__lte=today
        )

        count = 0
        for investment in expired:
            investment.status = 'completed'
            investment.save()

            AuditLog.objects.create(
                user=None,
                action='Investment Auto-Completed',
                model_name='Investment',
                object_id=investment.id,
                details=f"Investment {investment.id} for {investment.investor.user.username} auto-completed on {today}. End date was {investment.end_date}."
            )

            count += 1
            self.stdout.write(f'Completed investment {investment.id} — {investment.investor.user.username}')

        self.stdout.write(self.style.SUCCESS(f'Done. {count} investment(s) auto-completed.'))