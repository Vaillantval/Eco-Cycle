from django.db import migrations

CATEGORIES = [
    {'name': 'Plastique',       'slug': 'plastic',     'icon': '🧴', 'base_price_per_kg': 15},
    {'name': 'Métal / Ferraille','slug': 'metal',      'icon': '⚙️', 'base_price_per_kg': 45},
    {'name': 'Papier / Carton', 'slug': 'paper',       'icon': '📦', 'base_price_per_kg': 8},
    {'name': 'Électronique',    'slug': 'electronics', 'icon': '💻', 'base_price_per_kg': 120},
    {'name': 'Verre',           'slug': 'glass',       'icon': '🍶', 'base_price_per_kg': 5},
    {'name': 'Pneus',           'slug': 'tires',       'icon': '🛞', 'base_price_per_kg': 10},
    {'name': 'Autres déchets',  'slug': 'other',       'icon': '♻️', 'base_price_per_kg': 5},
]


def seed_categories(apps, schema_editor):
    WasteCategory = apps.get_model('waste', 'WasteCategory')
    for cat in CATEGORIES:
        WasteCategory.objects.get_or_create(
            slug=cat['slug'],
            defaults={
                'name':              cat['name'],
                'icon':              cat['icon'],
                'base_price_per_kg': cat['base_price_per_kg'],
                'is_active':         True,
            },
        )


def unseed_categories(apps, schema_editor):
    WasteCategory = apps.get_model('waste', 'WasteCategory')
    WasteCategory.objects.filter(slug__in=[c['slug'] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('waste', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=unseed_categories),
    ]
