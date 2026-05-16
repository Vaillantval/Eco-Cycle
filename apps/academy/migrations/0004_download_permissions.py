from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0003_lesson_pdf_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='pdf_allow_download',
            field=models.BooleanField(
                default=False,
                verbose_name='Autoriser le téléchargement du PDF',
                help_text="Si activé, l'utilisateur peut télécharger le fichier PDF original",
            ),
        ),
        migrations.AddField(
            model_name='lessonvideo',
            name='allow_download',
            field=models.BooleanField(
                default=False,
                verbose_name='Autoriser le téléchargement',
                help_text="Si activé, l'utilisateur peut télécharger le fichier vidéo (fichiers uploadés uniquement)",
            ),
        ),
    ]
