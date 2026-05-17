from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Sum
import uuid
import re


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='courses/', blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration_minutes = models.PositiveIntegerField(default=0)
    is_published        = models.BooleanField(default=False)
    price               = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    auto_advance_delay  = models.PositiveIntegerField(
        default=0,
        help_text='Secondes avant de passer automatiquement à la leçon suivante (0 = désactivé)',
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    @property
    def is_free(self):
        return self.price == 0

    class Meta:
        db_table = 'courses'
        ordering = ['created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def sync_duration(self):
        total = self.lessons.aggregate(total=Sum('duration_minutes'))['total'] or 0
        Course.objects.filter(pk=self.pk).update(duration_minutes=total)
        self.duration_minutes = total


class Lesson(models.Model):
    PDF_DISPLAY_EXTRACT = 'extract'
    PDF_DISPLAY_EMBED   = 'embed'
    PDF_DISPLAY_CHOICES = [
        ('extract', 'Extraire le texte (affichage texte)'),
        ('embed',   'Afficher le PDF tel quel (visionneuse)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    pdf_file = models.FileField(
        upload_to='academy/pdfs/', null=True, blank=True,
        verbose_name='PDF de la leçon',
    )
    pdf_display_mode = models.CharField(
        max_length=10,
        choices=PDF_DISPLAY_CHOICES,
        default='extract',
        verbose_name='Mode d\'affichage du PDF',
    )
    pdf_allow_download = models.BooleanField(
        default=False,
        verbose_name='Autoriser le téléchargement du PDF',
        help_text='Si activé, l\'utilisateur peut télécharger le fichier PDF original'
    )
    order = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)
    pdf_reading_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'

    def sync_duration(self):
        video_total = self.videos.aggregate(total=Sum('duration_minutes'))['total'] or 0
        total = video_total + self.pdf_reading_minutes
        Lesson.objects.filter(pk=self.pk).update(duration_minutes=total)
        self.duration_minutes = total
        self.course.sync_duration()


class LessonVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200, blank=True)
    video_file = models.FileField(
        upload_to='academy/videos/', null=True, blank=True,
        verbose_name='Fichier vidéo',
        help_text='MP4, WebM, OGG — max recommandé : 500 Mo'
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='URL vidéo externe',
        help_text='YouTube, Vimeo, ou tout lien direct'
    )
    allow_download = models.BooleanField(
        default=False,
        verbose_name='Autoriser le téléchargement',
        help_text='Si activé, l\'utilisateur peut télécharger le fichier vidéo (fichiers uploadés uniquement)'
    )
    order = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'lesson_videos'
        ordering = ['order']

    def __str__(self):
        return f'{self.lesson.title} — vidéo {self.order}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.lesson.sync_duration()

    def delete(self, *args, **kwargs):
        lesson = self.lesson
        super().delete(*args, **kwargs)
        lesson.sync_duration()

    def embed_url(self):
        """Return an embeddable URL for YouTube/Vimeo/TikTok, or None for direct files."""
        url = self.video_url
        if not url:
            return None
        # YouTube — enablejsapi=1 requis pour détecter la fin de lecture
        yt = re.search(r'(?:youtube\.com/(?:watch\?v=|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})', url)
        if yt:
            return f'https://www.youtube-nocookie.com/embed/{yt.group(1)}?rel=0&enablejsapi=1'
        # Vimeo — api=1 requis pour détecter la fin de lecture
        vm = re.search(r'vimeo\.com/(\d+)', url)
        if vm:
            return f'https://player.vimeo.com/video/{vm.group(1)}?api=1'
        # TikTok
        tt = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', url)
        if tt:
            return f'https://www.tiktok.com/embed/v2/{tt.group(1)}'
        return None

    def is_youtube(self):
        return bool(re.search(r'(?:youtube\.com|youtu\.be)', self.video_url or ''))

    def is_vimeo(self):
        return bool(re.search(r'vimeo\.com', self.video_url or ''))

    def is_tiktok(self):
        return bool(re.search(r'tiktok\.com', self.video_url or ''))


class Enrollment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('free',    'Gratuit'),
        ('pending', 'En attente de paiement'),
        ('paid',    'Payé'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    progress_percent = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='free')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_paid_or_free(self):
        return self.payment_status in ('paid', 'free')

    class Meta:
        db_table = 'enrollments'
        unique_together = ['user', 'course']

    def __str__(self):
        return f'{self.user.email} → {self.course.title}'

    def update_progress(self):
        total = self.course.lessons.count()
        if total == 0:
            self.progress_percent = 0
            self.save(update_fields=['progress_percent'])
            return
        done = self.completed_lessons.count()
        self.progress_percent = int((done / total) * 100)
        self.is_completed = done >= total
        if self.is_completed and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        self.save()


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'certificates'
        unique_together = ['user', 'course']

    def __str__(self):
        return f'{self.user.email} — {self.course.title}'
