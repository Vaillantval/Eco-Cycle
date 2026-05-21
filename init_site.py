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


def setup_periodic_tasks():
    """Synchronise les tâches périodiques Celery Beat dans la base (idempotent).
    Les schedules sont définis dans config/celery.py ; ici on s'assure qu'ils
    existent aussi en base pour le DatabaseScheduler de Railway.
    """
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        import json

        # Rappels de leçons non terminées — tous les jours à 10h00 UTC
        daily_10h, _ = CrontabSchedule.objects.get_or_create(
            minute='0', hour='10', day_of_week='*', day_of_month='*', month_of_year='*',
        )
        PeriodicTask.objects.update_or_create(
            name='Rappels leçons non terminées',
            defaults={
                'crontab': daily_10h,
                'task': 'notifications.send_lesson_reminders',
                'args': json.dumps([]),
                'enabled': True,
            },
        )
        print('✓ Periodic task "send_lesson_reminders" enregistrée.')
    except Exception as e:
        print(f'⚠ setup_periodic_tasks: {e}')


if __name__ == '__main__':
    create_superuser()
    setup_periodic_tasks()
