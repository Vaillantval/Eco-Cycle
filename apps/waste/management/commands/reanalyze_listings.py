from django.core.management.base import BaseCommand
from apps.waste.models import WasteListing
from apps.waste.tasks import analyze_waste_photo_async


class Command(BaseCommand):
    help = 'Re-lance l\'analyse IA sur les listings sans valeur estimée'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-analyser tous les listings (même ceux déjà analysés)')
        parser.add_argument('--id', type=str, help='Re-analyser un listing spécifique par ID')

    def handle(self, *args, **options):
        if options['id']:
            qs = WasteListing.objects.filter(id=options['id'])
        elif options['all']:
            qs = WasteListing.objects.filter(photo__isnull=False).exclude(photo='')
        else:
            qs = WasteListing.objects.filter(
                ai_estimated_value__isnull=True,
                photo__isnull=False,
            ).exclude(photo='')

        total = qs.count()
        self.stdout.write(f'{total} listing(s) à re-analyser...')

        for listing in qs:
            analyze_waste_photo_async.delay(str(listing.id))
            self.stdout.write(f'  → {listing.id} ({listing.title}) enqueued')

        self.stdout.write(self.style.SUCCESS(f'Done — {total} tâches envoyées à Celery.'))
