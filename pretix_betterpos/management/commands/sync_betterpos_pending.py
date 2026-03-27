from django.core.management.base import BaseCommand

from pretix_betterpos.models import BetterposTransaction


class Command(BaseCommand):
    help = 'Sync pending BetterPOS transactions using provider status checks (placeholder for euPago webhook fallback).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False)

    def handle(self, *args, **options):
        pending = BetterposTransaction.objects.filter(state=BetterposTransaction.STATE_PENDING).select_related('payment')
        self.stdout.write(f'Found {pending.count()} pending BetterPOS transactions')
        if options['dry_run']:
            self.stdout.write('Dry run complete')
            return

        for row in pending:
            self.stdout.write(f'Skipping transaction {row.id} (implement provider polling in next iteration)')

        self.stdout.write('Sync complete')
