import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ecocycle')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Clôturer les enchères expirées toutes les 5 minutes
    'close-expired-auctions': {
        'task': 'marketplace.close_expired_auctions',
        'schedule': 300.0,
    },
    # Rapport hebdomadaire admins — lundi 8h (heure Haïti)
    'weekly-admin-report': {
        'task': 'apps.core.tasks.send_weekly_report',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
    # Annuler les demandes de ramassage non assignées après 72h — toutes les heures
    'auto-cancel-unassigned-pickups': {
        'task': 'collections.auto_cancel_unassigned',
        'schedule': crontab(minute=0),
    },
    # Rappels leçons non terminées — tous les jours à 10h UTC
    'lesson-reminders': {
        'task': 'notifications.send_lesson_reminders',
        'schedule': crontab(hour=10, minute=0),
    },
    # Optimisation des prix des catégories — chaque lundi à minuit
    'run-price-optimizer': {
        'task': 'agents.run_price_optimizer',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),
    },
    # Scan anti-fraude — chaque jour à minuit
    'run-fraud-detector': {
        'task': 'agents.run_fraud_detector',
        'schedule': crontab(hour=0, minute=0),
    },
}
