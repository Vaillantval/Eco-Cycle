from django.db import models
import uuid


# ── Configuration globale du site (singleton) ────────────────────────────────

class SiteConfiguration(models.Model):

    # Identité
    site_name   = models.CharField(max_length=100, default='EcoCycle Haiti', verbose_name='Nom du site')
    tagline     = models.CharField(max_length=200, default='Recyclez, Gagnez, Impactez', verbose_name='Slogan')
    logo        = models.ImageField(upload_to='site/logo/', null=True, blank=True, verbose_name='Logo', help_text='PNG transparent, 200×60 px min')
    favicon     = models.ImageField(upload_to='site/favicon/', null=True, blank=True, verbose_name='Favicon', help_text='ICO ou PNG 32×32 px')

    # Hero
    hero_badge    = models.CharField(max_length=100, default='🇭🇹 Pionnier du Recyclage en Haïti', blank=True, verbose_name='Texte badge hero')
    hero_title_1  = models.CharField(max_length=200, default='Transformez Vos Déchets', blank=True, verbose_name='Hero — titre ligne 1')
    hero_title_2  = models.CharField(max_length=200, default='En Trésor', blank=True, verbose_name='Hero — titre ligne 2')
    hero_subtitle = models.TextField(default='Achetez et vendez des matériaux recyclables via des enchères sécurisées. Rejoignez l\'économie circulaire d\'Haïti — propulsé par l\'IA.', blank=True, verbose_name='Hero — sous-titre')

    # Contact
    contact_email = models.EmailField(default='info@ecocycle.ht', blank=True, verbose_name='Email de contact')
    contact_phone = models.CharField(max_length=30, blank=True, verbose_name='Téléphone')
    whatsapp      = models.CharField(max_length=30, blank=True, verbose_name='WhatsApp', help_text='+509 XXXX-XXXX')
    address       = models.TextField(blank=True, verbose_name='Adresse physique')
    hours         = models.CharField(max_length=200, blank=True, verbose_name='Horaires', help_text='Ex: Lun–Ven 8h–17h')

    # Réseaux sociaux
    facebook_url  = models.URLField(blank=True, verbose_name='Facebook URL')
    instagram_url = models.URLField(blank=True, verbose_name='Instagram URL')
    twitter_url   = models.URLField(blank=True, verbose_name='Twitter / X URL')
    youtube_url   = models.URLField(blank=True, verbose_name='YouTube URL')
    linkedin_url  = models.URLField(blank=True, verbose_name='LinkedIn URL')

    # Application mobile
    android_apk_url    = models.URLField(blank=True, verbose_name='Google Play URL')
    ios_store_url      = models.URLField(blank=True, verbose_name='App Store URL')
    android_direct_apk = models.FileField(upload_to='android/', null=True, blank=True, verbose_name='APK direct (.apk)', help_text='Fichier .apk à télécharger directement')

    # SEO & Footer
    meta_description    = models.TextField(blank=True, verbose_name='Meta description (SEO)', help_text='160 caractères max')
    google_analytics_id = models.CharField(max_length=50, blank=True, verbose_name='Google Analytics ID', help_text='G-XXXXXXXXXX')
    copyright_text      = models.CharField(max_length=300, default='EcoCycle Haiti © 2026. Tous droits réservés.', blank=True, verbose_name='Texte copyright')

    # Maintenance
    maintenance_mode    = models.BooleanField(default=False, verbose_name='Mode maintenance')
    maintenance_message = models.TextField(blank=True, verbose_name='Message de maintenance')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Configuration du site'
        verbose_name_plural = 'Configuration du site'

    def __str__(self):
        return f'Configuration — {self.site_name}'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


# ── Slider items (géré depuis l'admin) ──────────────────────────────────────

class SliderItem(models.Model):
    icon        = models.CharField(max_length=10, default='♻️', verbose_name='Icône (emoji)')
    tag         = models.CharField(max_length=80, blank=True, verbose_name='Étiquette (ex: Intelligence artificielle)')
    title       = models.CharField(max_length=120, verbose_name='Titre')
    description = models.TextField(verbose_name='Description')
    cta_text    = models.CharField(max_length=60, default='En savoir plus →', blank=True, verbose_name='Texte du lien')
    cta_url     = models.CharField(max_length=255, blank=True, verbose_name='URL du lien', help_text='URL relative ou absolue')
    ordre       = models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')
    is_active   = models.BooleanField(default=True, verbose_name='Actif')

    class Meta:
        verbose_name        = 'Slide'
        verbose_name_plural = 'Slides (page d\'accueil)'
        ordering            = ['ordre']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    replied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contact_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.subject}'


class NewsletterSubscriber(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_confirmed = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'newsletter_subscribers'

    def __str__(self):
        return f'{self.email} ({"confirmé" if self.is_confirmed else "non confirmé"})'
