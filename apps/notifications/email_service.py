import logging
import resend
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


class EmailService:

    @staticmethod
    def _logo_url() -> str:
        """Retourne l'URL absolue du logo si configuré, sinon chaîne vide."""
        try:
            from apps.core.models import SiteConfiguration
            config = SiteConfiguration.get_solo()
            if config.logo:
                return settings.FRONTEND_URL.rstrip('/') + config.logo.url
        except Exception:
            pass
        return ''

    @classmethod
    def _render_email(cls, template: str, ctx: dict) -> str:
        """render_to_string avec logo_url + frontend_url injectés automatiquement."""
        base = {
            'frontend_url': settings.FRONTEND_URL,
            'logo_url': cls._logo_url(),
        }
        return render_to_string(template, {**base, **ctx})

    @staticmethod
    def _send(to: str, subject: str, html: str):
        try:
            resend.Emails.send({
                'from': f'{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>',
                'to': [to],
                'subject': subject,
                'html': html,
            })
        except Exception as e:
            logger.error(f'Email send error to {to}: {e}')

    @classmethod
    def send_welcome(cls, user, verify_url: str):
        html = cls._render_email('emails/welcome.html', {
            'user': user,
            'verify_url': verify_url,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(user.email, 'Bienvenue sur EcoCycle Haiti !', html)

    @classmethod
    def send_verification(cls, user, verify_url: str):
        html = cls._render_email('emails/verify_email.html', {
            'user': user,
            'verify_url': verify_url,
        })
        cls._send(user.email, 'Verifiez votre adresse email — EcoCycle', html)

    @classmethod
    def send_password_reset(cls, user, reset_url: str):
        html = cls._render_email('emails/reset_password.html', {
            'user': user,
            'reset_url': reset_url,
        })
        cls._send(user.email, 'Reinitialisation de votre mot de passe — EcoCycle', html)

    @classmethod
    def send_listing_approved(cls, listing):
        html = cls._render_email('emails/listing_approved.html', {
            'user': listing.user,
            'listing': listing,
            'marketplace_url': f'{settings.FRONTEND_URL}/marketplace',
        })
        cls._send(listing.user.email, 'Votre listing a ete approuve — EcoCycle', html)

    @classmethod
    def send_listing_rejected(cls, listing):
        html = cls._render_email('emails/listing_approved.html', {
            'user': listing.user,
            'listing': listing,
            'reason': listing.rejection_reason,
            'rejected': True,
        })
        cls._send(listing.user.email, "Votre listing n'a pas ete approuve — EcoCycle", html)

    @classmethod
    def send_auction_won(cls, order):
        html = cls._render_email('emails/auction_won.html', {
            'user': order.buyer,
            'order': order,
            'listing': order.auction.listing,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(order.buyer.email, "Vous avez remporte l'enchere ! — EcoCycle", html)

    @classmethod
    def send_pickup_confirmed(cls, pickup):
        html = cls._render_email('emails/pickup_confirmed.html', {
            'user': pickup.user,
            'pickup': pickup,
        })
        cls._send(pickup.user.email, 'Votre ramassage est confirme — EcoCycle', html)

    @classmethod
    def send_admin_new_listing(cls, admin, listing):
        html = cls._render_email('emails/listing_approved.html', {
            'admin': admin,
            'listing': listing,
            'review_url': f'{settings.FRONTEND_URL}/admin/listings/{listing.id}',
            'admin_notification': True,
        })
        cls._send(
            admin.email,
            f'[EcoCycle Admin] Nouveau listing a reviser : {listing.title}',
            html,
        )

    @classmethod
    def send_admin_new_user(cls, admin, new_user):
        html = (
            f'<p>Bonjour {admin.first_name},</p>'
            f'<p>Un nouvel utilisateur vient de s\'inscrire sur EcoCycle :</p>'
            f'<p><strong>{new_user.full_name}</strong> — {new_user.email}</p>'
            f'<p>Inscrit le : {new_user.date_joined.strftime("%d/%m/%Y à %H:%M")}</p>'
            f'<p><a href="{settings.FRONTEND_URL}/panel/users/">Voir les utilisateurs</a></p>'
        )
        cls._send(admin.email, f'[EcoCycle Admin] Nouvel utilisateur : {new_user.full_name}', html)

    @classmethod
    def send_admin_payment_received(cls, admin, transaction):
        if transaction.order_id:
            label = f'Commande marketplace — {transaction.order.auction.listing.title}'
            buyer_name = transaction.order.buyer.full_name
            detail_url = f'{settings.FRONTEND_URL}/panel/orders/{transaction.order.id}/'
        else:
            label = f'Cours Academy — {transaction.enrollment.course.title}'
            buyer_name = transaction.enrollment.user.full_name
            detail_url = f'{settings.FRONTEND_URL}/panel/academy/'
        html = (
            f'<p>Bonjour {admin.first_name},</p>'
            f'<p>Un paiement a été confirmé sur EcoCycle :</p>'
            f'<p><strong>{buyer_name}</strong> — {transaction.amount} HTG</p>'
            f'<p>Objet : {label}</p>'
            f'<p>Méthode : {transaction.get_payment_method_display()}</p>'
            f'<p>Ref : {transaction.transaction_number}</p>'
            f'<p><a href="{detail_url}">Voir les détails</a></p>'
        )
        cls._send(admin.email, f'[EcoCycle Admin] Paiement reçu — {transaction.amount} HTG', html)

    @classmethod
    def send_admin_pickup_failed(cls, admin, pickup):
        collector_name = pickup.collector.full_name if pickup.collector else 'Non assigné'
        html = (
            f'<p>Bonjour {admin.first_name},</p>'
            f'<p>Un ramassage a été marqué comme <strong>échoué</strong> :</p>'
            f'<p>Client : <strong>{pickup.user.full_name}</strong></p>'
            f'<p>Ville : {pickup.city}</p>'
            f'<p>Date prévue : {pickup.preferred_date}</p>'
            f'<p>Collecteur : {collector_name}</p>'
            f'<p><a href="{settings.FRONTEND_URL}/panel/collections/{pickup.id}/">Voir le ramassage</a></p>'
        )
        cls._send(admin.email, f'[EcoCycle Admin] Ramassage échoué — {pickup.user.full_name}', html)

    @classmethod
    def send_admin_paid_enrollment(cls, admin, enrollment):
        html = (
            f'<p>Bonjour {admin.first_name},</p>'
            f'<p>Un utilisateur vient de s\'inscrire à un cours payant :</p>'
            f'<p>Étudiant : <strong>{enrollment.user.full_name}</strong> ({enrollment.user.email})</p>'
            f'<p>Cours : <strong>{enrollment.course.title}</strong></p>'
            f'<p>Prix : {enrollment.course.price} HTG</p>'
            f'<p><a href="{settings.FRONTEND_URL}/panel/academy/{enrollment.course.id}/">Voir le cours</a></p>'
        )
        cls._send(
            admin.email,
            f'[EcoCycle Admin] Inscription payante — {enrollment.user.full_name} — {enrollment.course.title}',
            html,
        )

    @classmethod
    def send_newsletter_confirmation(cls, subscriber):
        html = cls._render_email('emails/newsletter_confirm.html', {
            'subscriber': subscriber,
            'confirm_url': f'{settings.FRONTEND_URL}/newsletter/confirm/{subscriber.token}',
        })
        cls._send(subscriber.email, 'Confirmez votre abonnement — EcoCycle', html)

    @classmethod
    def send_certificate_earned(cls, user, course, certificate):
        html = cls._render_email('emails/certificate_earned.html', {
            'user': user,
            'course': course,
            'certificate': certificate,
            'certificates_url': f'{settings.FRONTEND_URL}/dashboard/certificates/',
            'academy_url': f'{settings.FRONTEND_URL}/academy/',
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(user.email, f'Félicitations ! Votre certificat « {course.title} » est prêt — EcoCycle', html)

    @classmethod
    def send_maintenance_over(cls, user, message: str = ''):
        html = cls._render_email('emails/maintenance_over.html', {
            'user': user,
            'message': message,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(user.email, 'EcoCycle est de retour ! — Le site est à nouveau disponible', html)

    @classmethod
    def send_order_confirmation(cls, order, transaction):
        html = cls._render_email('emails/order_confirmation.html', {
            'user':        order.buyer,
            'order':       order,
            'transaction': transaction,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(
            order.buyer.email,
            f'✅ Paiement confirmé — Commande #{str(order.id)[:8]} — EcoCycle Haiti',
            html,
        )

    @classmethod
    def send_order_paid_seller(cls, order):
        html = cls._render_email('emails/order_paid_seller.html', {
            'user':       order.seller,
            'order':      order,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(
            order.seller.email,
            f'💰 Votre article a été vendu — EcoCycle Haiti',
            html,
        )

    @classmethod
    def send_admin_course_completed(cls, admin, user, course, certificate):
        html = cls._render_email('emails/admin_course_completed.html', {
            'admin': admin,
            'user': user,
            'course': course,
            'certificate': certificate,
            'admin_url': f'{settings.FRONTEND_URL}/panel/academy/certificates/',
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(
            admin.email,
            f'[EcoCycle] {user.full_name} a complété « {course.title} »',
            html,
        )

    @classmethod
    def send_course_enrollment_confirmation(cls, enrollment, transaction):
        course = enrollment.course
        user   = enrollment.user
        html = cls._render_email('emails/course_enrollment_confirmation.html', {
            'user':        user,
            'course':      course,
            'transaction': transaction,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(
            user.email,
            f'Inscription confirmée — {course.title}',
            html,
        )
