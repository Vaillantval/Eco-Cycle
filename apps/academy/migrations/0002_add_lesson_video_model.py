import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0001_initial'),
    ]

    operations = [
        # Make content blank on Lesson
        migrations.AlterField(
            model_name='lesson',
            name='content',
            field=models.TextField(blank=True),
        ),
        # Remove video_url from Lesson
        migrations.RemoveField(
            model_name='lesson',
            name='video_url',
        ),
        # Add LessonVideo model
        migrations.CreateModel(
            name='LessonVideo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('video_file', models.FileField(
                    blank=True, null=True,
                    upload_to='academy/videos/',
                    verbose_name='Fichier vidéo',
                    help_text='MP4, WebM, OGG — max recommandé : 500 Mo',
                )),
                ('video_url', models.URLField(
                    blank=True,
                    verbose_name='URL vidéo externe',
                    help_text='YouTube, Vimeo, ou tout lien direct',
                )),
                ('order', models.PositiveIntegerField(default=0)),
                ('duration_minutes', models.PositiveIntegerField(default=0)),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='videos',
                    to='academy.lesson',
                )),
            ],
            options={
                'db_table': 'lesson_videos',
                'ordering': ['order'],
            },
        ),
    ]
