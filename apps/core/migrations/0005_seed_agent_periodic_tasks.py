from django.db import migrations


AGENT_TASKS = [
    {
        'name': 'run-price-optimizer',
        'task': 'agents.run_price_optimizer',
        'description': 'Optimise les prix des catégories de déchets en analysant les transactions récentes.',
        'minute': '0',
        'hour': '0',
        'day_of_week': '1',  # lundi
        'day_of_month': '*',
        'month_of_year': '*',
    },
    {
        'name': 'run-fraud-detector',
        'task': 'agents.run_fraud_detector',
        'description': 'Détecte les comportements suspects et bloque automatiquement les comptes à haut risque.',
        'minute': '0',
        'hour': '0',
        'day_of_week': '*',  # tous les jours
        'day_of_month': '*',
        'month_of_year': '*',
    },
    {
        'name': 'run-academy-curator',
        'task': 'agents.run_academy_curator',
        'description': 'Recherche des vidéos YouTube sur le recyclage et génère des suggestions de cours.',
        'minute': '0',
        'hour': '9',
        'day_of_week': '1',  # lundi
        'day_of_month': '*',
        'month_of_year': '*',
    },
    {
        'name': 'run-blog-writer',
        'task': 'agents.run_blog_writer',
        'description': 'Recherche des actualités environnementales et suggère des angles d\'articles.',
        'minute': '30',
        'hour': '8',
        'day_of_week': '3',  # mercredi
        'day_of_month': '*',
        'month_of_year': '*',
    },
]


def seed_agent_tasks(apps, schema_editor):
    CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    for task_def in AGENT_TASKS:
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=task_def['minute'],
            hour=task_def['hour'],
            day_of_week=task_def['day_of_week'],
            day_of_month=task_def['day_of_month'],
            month_of_year=task_def['month_of_year'],
            timezone='America/Port-au-Prince',
        )
        PeriodicTask.objects.get_or_create(
            name=task_def['name'],
            defaults={
                'task': task_def['task'],
                'crontab': crontab,
                'description': task_def['description'],
                'enabled': True,
            },
        )


def remove_agent_tasks(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(
        name__in=[t['name'] for t in AGENT_TASKS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_ios_ipa_remove_url_fields'),
        ('django_celery_beat', '0018_improve_crontab_helptext'),
    ]

    operations = [
        migrations.RunPython(seed_agent_tasks, remove_agent_tasks),
    ]
