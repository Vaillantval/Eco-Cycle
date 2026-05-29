import time
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.accounts.geocoding_service import geocode_address


class Command(BaseCommand):
    help = 'Géocode tous les utilisateurs existants qui ont une adresse/ville mais pas de coordonnées.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regéocoder même les users qui ont déjà des coordonnées.',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.1,
            help='Délai entre chaque requête Nominatim en secondes (défaut: 1.1).',
        )

    def handle(self, *args, **options):
        force  = options['all']
        delay  = options['delay']

        qs = User.objects.exclude(address='', city='')
        if not force:
            qs = qs.filter(latitude__isnull=True)

        total   = qs.count()
        success = 0
        failed  = 0

        self.stdout.write(f'→ {total} utilisateur(s) à géocoder...\n')

        for user in qs.iterator():
            result = geocode_address(user.address, user.city)
            if result:
                lat, lon = result
                User.objects.filter(pk=user.pk).update(latitude=lat, longitude=lon)
                success += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {user.email} → ({lat:.5f}, {lon:.5f})')
                )
            else:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(f'  ✗ {user.email} — introuvable ({user.address!r}, {user.city!r})')
                )

            time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(f'\nTerminé : {success} géocodés, {failed} introuvables sur {total}.')
        )
