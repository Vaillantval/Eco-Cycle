"""
Script d'initialisation EcoCycle — exécuté au démarrage Railway.
Idempotent : peut être relancé sans risque.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.contrib.auth import get_user_model


def create_superuser():
    User = get_user_model()
    email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
    if not email or not password:
        print('⚠ DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD non définis — superuser ignoré.')
        return
    if User.objects.filter(email=email).exists():
        print(f'✓ Superuser {email} existe déjà.')
        return
    User.objects.create_superuser(
        email=email,
        password=password,
        first_name=os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin'),
        last_name=os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'EcoCycle'),
    )
    print(f'✓ Superuser {email} créé.')


if __name__ == '__main__':
    create_superuser()
