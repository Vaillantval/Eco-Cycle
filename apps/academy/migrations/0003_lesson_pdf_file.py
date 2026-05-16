from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0002_add_lesson_video_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='pdf_file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='academy/pdfs/',
                verbose_name='PDF de la leçon',
                help_text='Upload un PDF pour extraire automatiquement le texte',
            ),
        ),
    ]
