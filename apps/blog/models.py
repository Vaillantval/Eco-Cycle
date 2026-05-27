from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid


class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = 'blog_categories'
        verbose_name_plural = 'Blog Categories'

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts'
    )
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, blank=True, max_length=320)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    cover_image = models.ImageField(upload_to='blog/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    read_time_minutes = models.PositiveIntegerField(default=5)
    views = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_posts'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class BlogRecommendation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('published', 'Publié'),
    ]

    suggested_title = models.CharField(max_length=300)
    seo_title = models.CharField(max_length=60, blank=True)
    angle = models.TextField()
    sources = models.JSONField(default=list)
    generated_content = models.TextField(blank=True)
    excerpt = models.TextField(blank=True, max_length=500)
    tags = models.JSONField(default=list)
    estimated_read_time = models.PositiveIntegerField(default=5)
    word_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_post = models.OneToOneField(
        'Post', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='recommendation',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'blog_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.suggested_title} ({self.get_status_display()})'
