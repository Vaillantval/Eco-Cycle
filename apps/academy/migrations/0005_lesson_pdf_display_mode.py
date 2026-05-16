from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0004_download_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='pdf_display_mode',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('extract', "Extraire le texte (affichage texte)"),
                    ('embed',   "Afficher le PDF tel quel (visionneuse)"),
                ],
                default='extract',
                verbose_name="Mode d'affichage du PDF",
            ),
        ),
    ]
