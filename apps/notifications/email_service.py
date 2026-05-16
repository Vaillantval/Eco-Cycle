import logging
import resend
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


class EmailService:

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
        html = render_to_string('emails/welcome.html', {
            'user': user,
            'verify_url': verify_url,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(user.email, 'Bienvenue sur EcoCycle Haiti !', html)

    @classmethod
    def send_verification(cls, user, verify_url: str):
        html = render_to_string('emails/verify_email.html', {
            'user': user,
            'verify_url': verify_url,
        })
        cls._send(user.email, 'Verifiez votre adresse email — EcoCycle', html)

    @classmethod
    def send_password_reset(cls, user, reset_url: str):
        html = render_to_string('emails/reset_password.html', {
            'user': user,
            'reset_url': reset_url,
        })
        cls._send(user.email, 'Reinitialisation de votre mot de passe — EcoCycle', html)

    @classmethod
    def send_listing_approved(cls, listing):
        html = render_to_string('emails/listing_approved.html', {
            'user': listing.user,
            'listing': listing,
            'marketplace_url': f'{settings.FRONTEND_URL}/marketplace',
        })
        cls._send(listing.user.email, 'Votre listing a ete approuve — EcoCycle', html)

    @classmethod
    def send_listing_rejected(cls, listing):
        html = render_to_string('emails/listing_approved.html', {
            'user': listing.user,
            'listing': listing,
            'reason': listing.rejection_reason,
            'rejected': True,
        })
        cls._send(listing.user.email, "Votre listing n'a pas ete approuve — EcoCycle", html)

    @classmethod
    def send_auction_won(cls, order):
        html = render_to_string('emails/auction_won.html', {
            'user': order.buyer,
            'order': order,
            'listing': order.auction.listing,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(order.buyer.email, "Vous avez remporte l'enchere ! — EcoCycle", html)

    @classmethod
    def send_pickup_confirmed(cls, pickup):
        html = render_to_string('emails/pickup_confirmed.html', {
            'user': pickup.user,
            'pickup': pickup,
        })
        cls._send(pickup.user.email, 'Votre ramassage est confirme — EcoCycle', html)

    @classmethod
    def send_admin_new_listing(cls, admin, listing):
        html = render_to_string('emails/listing_approved.html', {
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
    def send_newsletter_confirmation(cls, subscriber):
        html = render_to_string('emails/newsletter_confirm.html', {
            'subscriber': subscriber,
            'confirm_url': f'{settings.FRONTEND_URL}/newsletter/confirm/{subscriber.token}',
        })
        cls._send(subscriber.email, 'Confirmez votre abonnement — EcoCycle', html)

    @classmethod
    def send_certificate_earned(cls, user, course, certificate):
        html = render_to_string('emails/certificate_earned.html', {
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
        html = render_to_string('emails/maintenance_over.html', {
            'user': user,
            'message': message,
            'frontend_url': settings.FRONTEND_URL,
        })
        cls._send(user.email, 'EcoCycle est de retour ! — Le site est à nouveau disponible', html)

    @classmethod
    def send_order_confirmation(cls, order, transaction):
        html = render_to_string('emails/order_confirmation.html', {
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
        html = render_to_string('emails/order_paid_seller.html', {
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
        html = render_to_string('emails/admin_course_completed.html', {
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
        html = render_to_string('emails/course_enrollment_confirmation.html', {
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
