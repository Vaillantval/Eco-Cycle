from django.db import migrations


def reset_stuck_recommendations(apps, schema_editor):
    """Remet en 'pending' les CourseRecommendation approuvées mais sans cours créé
    (elles ont échoué à cause du bug slug trop long, maintenant corrigé)."""
    CourseRecommendation = apps.get_model('academy', 'CourseRecommendation')
    stuck = CourseRecommendation.objects.filter(
        status='approved',
        created_course__isnull=True,
    )
    count = stuck.update(status='pending', reviewed_at=None)
    if count:
        print(f'  Réinitialisé {count} recommandation(s) bloquée(s) → pending')


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0010_increase_course_slug_max_length'),
    ]

    operations = [
        migrations.RunPython(reset_stuck_recommendations, migrations.RunPython.noop),
    ]
