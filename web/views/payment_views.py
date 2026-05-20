import json
import logging
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from web.mixins import LoginRequiredMixin
from apps.marketplace.models import Order
from apps.payments.models import Transaction
from apps.payments.stripe_service import StripeService
from apps.payments.plopplop_service import PlopPlopService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
#  Fonction centrale — activée dès que le paiement est confirmé
# ─────────────────────────────────────────────────────────

def process_successful_payment(transaction: Transaction, external_id: str = '', method: str = ''):
    """
    Point central de confirmation de paiement — idempotent.
    Gère deux cas :
      - transaction.order       → commande marketplace
      - transaction.enrollment  → inscription cours academy
    """
    if transaction.status == 'completed':
        return

    if external_id:
        transaction.external_transaction_id = external_id
    if method:
        transaction.payment_method = method
    transaction.status       = 'completed'
    transaction.completed_at = timezone.now()
    transaction.save(update_fields=['status', 'payment_method', 'external_transaction_id', 'completed_at', 'updated_at'])

    # ── Cas 1 : commande marketplace ──────────────────────────────────────────
    if transaction.order_id:
        order = transaction.order
        order.status = 'paid'
        order.save(update_fields=['status', 'updated_at'])

        try:
            from apps.notifications.email_service import EmailService
            EmailService.send_order_confirmation(order, transaction)
        except Exception as e:
            logger.warning(f'[Payment] Email commande non envoyé ({order.id}): {e}')

        try:
            from apps.notifications.tasks import notify_order_paid
            notify_order_paid.delay(str(order.id))
        except Exception as e:
            logger.warning(f'[Payment] Notif order_paid non envoyée: {e}')

        try:
            from apps.notifications.tasks import notify_admin_payment_received
            notify_admin_payment_received.delay(str(transaction.id))
        except Exception as e:
            logger.warning(f'[Payment] Notif admin_payment non envoyée: {e}')

    # ── Cas 2 : inscription cours payant ─────────────────────────────────────
    elif transaction.enrollment_id:
        enrollment = transaction.enrollment
        enrollment.payment_status = 'paid'
        enrollment.save(update_fields=['payment_status'])

        try:
            from apps.notifications.email_service import EmailService
            EmailService.send_course_enrollment_confirmation(enrollment, transaction)
        except Exception as e:
            logger.warning(f'[Payment] Email inscription cours non envoyé ({enrollment.id}): {e}')

        try:
            from apps.notifications.tasks import notify_admin_payment_received, notify_admin_paid_enrollment
            notify_admin_payment_received.delay(str(transaction.id))
            notify_admin_paid_enrollment.delay(str(enrollment.id))
        except Exception as e:
            logger.warning(f'[Payment] Notif admin_enrollment non envoyée: {e}')


def _payment_success_response(request, transaction: Transaction, method_label: str):
    """Renvoie la bonne page de succès selon le type de transaction."""
    if transaction.order_id:
        return render(request, 'payments/success.html', {
            'order':        transaction.order,
            'transaction':  transaction,
            'method_label': method_label,
        })
    enrollment = transaction.enrollment
    return render(request, 'payments/course_success.html', {
        'course':       enrollment.course,
        'enrollment':   enrollment,
        'transaction':  transaction,
        'method_label': method_label,
    })


# ─────────────────────────────────────────────────────────
#  Page de sélection du mode de paiement
# ─────────────────────────────────────────────────────────

class PaymentCheckoutView(LoginRequiredMixin, View):
    """GET /payment/<order_id>/ — choisir Stripe ou PlopPlop"""

    def get(self, request, order_id):
        user  = self.get_current_user(request)
        order = get_object_or_404(Order, id=order_id, buyer=user)

        if order.status != 'pending_payment':
            messages.info(request, 'Cette commande a déjà été traitée.')
            return redirect('my_orders')

        # Récupérer ou créer la transaction
        transaction, _ = Transaction.objects.get_or_create(
            order=order,
            defaults={'amount': order.amount, 'currency': 'HTG'},
        )

        return render(request, 'payments/checkout.html', {
            'order':       order,
            'transaction': transaction,
        })


# ─────────────────────────────────────────────────────────
#  Stripe
# ─────────────────────────────────────────────────────────

class StripeInitView(LoginRequiredMixin, View):
    """POST /payment/<order_id>/stripe/init/ — crée le PaymentIntent"""

    def post(self, request, order_id):
        user  = self.get_current_user(request)
        order = get_object_or_404(Order, id=order_id, buyer=user, status='pending_payment')

        transaction, _ = Transaction.objects.get_or_create(
            order=order,
            defaults={'amount': order.amount, 'currency': 'HTG'},
        )

        if transaction.status == 'completed':
            return JsonResponse({'error': 'Déjà payé.'}, status=400)

        # Réutiliser le PaymentIntent existant si présent
        existing_pi = transaction.meta_data.get('stripe_payment_intent_id')
        if existing_pi:
            svc    = StripeService()
            result = svc.retrieve_payment_intent(existing_pi)
            if result['success'] and result['status'] not in ('canceled', 'requires_payment_method'):
                return JsonResponse({
                    'success': True,
                    'client_secret': transaction.meta_data.get('stripe_client_secret'),
                    'transaction_number': transaction.transaction_number,
                })

        svc    = StripeService()
        result = svc.create_payment_intent(
            amount_htg=float(order.amount),
            transaction_number=transaction.transaction_number,
            metadata={'order_id': str(order.id)},
        )

        if not result['success']:
            return JsonResponse({'error': result.get('error', 'Erreur Stripe')}, status=502)

        transaction.meta_data['stripe_payment_intent_id'] = result['payment_intent_id']
        transaction.meta_data['stripe_client_secret']     = result['client_secret']
        transaction.payment_method = 'credit_card'
        transaction.save(update_fields=['meta_data', 'payment_method', 'updated_at'])

        return JsonResponse({
            'success': True,
            'client_secret': result['client_secret'],
            'transaction_number': transaction.transaction_number,
        })


class StripeCheckoutView(LoginRequiredMixin, View):
    """GET /payment/<order_id>/stripe/checkout/ — page Stripe Elements"""

    def get(self, request, order_id):
        from django.conf import settings
        user  = self.get_current_user(request)
        order = get_object_or_404(Order, id=order_id, buyer=user)
        transaction = get_object_or_404(Transaction, order=order)

        return render(request, 'payments/stripe_checkout.html', {
            'order':       order,
            'transaction': transaction,
            'stripe_public_key': settings.STRIPE['PUBLIC_KEY'],
        })


class StripeSuccessView(LoginRequiredMixin, View):
    """GET /payment/stripe/success/?payment_intent=pi_xxx — retour Stripe"""

    def get(self, request):
        pi_id = request.GET.get('payment_intent', '')
        if not pi_id:
            messages.error(request, 'Paiement invalide.')
            return redirect('my_orders')

        svc    = StripeService()
        result = svc.retrieve_payment_intent(pi_id)

        if not result['success'] or result['status'] != 'succeeded':
            messages.error(request, 'Le paiement n\'a pas abouti. Réessayez.')
            return redirect('my_orders')

        tx_number = result.get('transaction_number', '')
        try:
            transaction = Transaction.objects.select_related('order').get(
                transaction_number=tx_number
            )
        except Transaction.DoesNotExist:
            messages.error(request, 'Transaction introuvable.')
            return redirect('my_orders')

        process_successful_payment(transaction, external_id=pi_id, method='credit_card')
        return _payment_success_response(request, transaction, 'Carte bancaire (Stripe)')


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """POST /api/payments/stripe/webhook/ — webhook Stripe (CSRF-exempt)"""

    def post(self, request):
        sig_header = request.headers.get('Stripe-Signature', '')
        svc        = StripeService()
        result     = svc.construct_webhook_event(request.body, sig_header)

        if not result['success']:
            return HttpResponse(status=400)

        event = result['event']
        if event['type'] == 'payment_intent.succeeded':
            pi   = event['data']['object']
            tx_number = pi['metadata'].get('transaction_number', '')
            try:
                transaction = Transaction.objects.select_related('order').get(
                    transaction_number=tx_number
                )
                process_successful_payment(transaction, external_id=pi['id'], method='credit_card')
            except Transaction.DoesNotExist:
                logger.warning(f'[StripeWebhook] Transaction introuvable: {tx_number}')
            except Exception as e:
                logger.error(f'[StripeWebhook] Erreur process: {e}')

        return HttpResponse(status=200)


# ─────────────────────────────────────────────────────────
#  PlopPlop
# ─────────────────────────────────────────────────────────

class PlopPlopInitiateView(LoginRequiredMixin, View):
    """POST /payment/<order_id>/plopplop/ — crée le paiement et redirige"""

    def post(self, request, order_id):
        user   = self.get_current_user(request)
        order  = get_object_or_404(Order, id=order_id, buyer=user, status='pending_payment')
        method = request.POST.get('method', 'all')  # moncash | natcash | kashpaw | all

        transaction, _ = Transaction.objects.get_or_create(
            order=order,
            defaults={'amount': order.amount, 'currency': 'HTG'},
        )

        if transaction.status == 'completed':
            messages.info(request, 'Cette commande est déjà payée.')
            return redirect('my_orders')

        svc    = PlopPlopService()
        result = svc.create_payment(
            reference_id=transaction.transaction_number,
            montant=float(order.amount),
            payment_method=method,
        )

        if not result['success']:
            messages.error(request, f'Erreur PlopPlop : {result.get("error", "Réessayez.")}')
            return redirect('payment_checkout', order_id=order_id)

        transaction.payment_method = method if method != 'all' else 'moncash'
        transaction.meta_data['plopplop_url']            = result['url']
        transaction.meta_data['plopplop_transaction_id'] = result.get('transaction_id', '')
        transaction.save(update_fields=['payment_method', 'meta_data', 'updated_at'])

        return redirect(result['url'])


class PlopPlopReturnView(View):
    """GET|POST /payment/plopplop/retour/ — retour utilisateur après PlopPlop"""

    def get(self, request):
        return self._handle(request)

    def post(self, request):
        return self._handle(request)

    def _handle(self, request):
        reference_id = request.GET.get('reference_id') or request.POST.get('reference_id', '')
        if not reference_id:
            messages.error(request, 'Référence de paiement manquante.')
            return redirect('my_orders')

        try:
            transaction = Transaction.objects.select_related('order').get(
                transaction_number=reference_id
            )
        except Transaction.DoesNotExist:
            messages.error(request, 'Transaction introuvable.')
            return redirect('my_orders')

        method_label = transaction.get_payment_method_display()

        if transaction.status == 'completed':
            return _payment_success_response(request, transaction, method_label)

        svc    = PlopPlopService()
        result = svc.verify_payment(reference_id)

        if not result['success'] or not result['paid']:
            messages.error(request, 'Le paiement n\'a pas été confirmé par PlopPlop. Réessayez.')
            if transaction.order_id:
                return redirect('payment_checkout', order_id=transaction.order.id)
            return redirect('course_checkout', slug=transaction.enrollment.course.slug)

        process_successful_payment(
            transaction,
            external_id=result.get('id_transaction', ''),
            method=result.get('method', transaction.payment_method),
        )
        return _payment_success_response(request, transaction, method_label)


@method_decorator(csrf_exempt, name='dispatch')
class PlopPlopWebhookView(View):
    """POST /api/payments/plopplop/webhook/ — webhook PlopPlop (CSRF-exempt)"""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return HttpResponse(status=400)

        reference_id = data.get('reference_id') or data.get('refference_id', '')
        if not reference_id:
            return HttpResponse(status=400)

        try:
            transaction = Transaction.objects.select_related('order').get(
                transaction_number=reference_id
            )
        except Transaction.DoesNotExist:
            logger.warning(f'[PlopPlopWebhook] Transaction introuvable: {reference_id}')
            return HttpResponse(status=404)

        if transaction.status == 'completed':
            return JsonResponse({'status': 'already_processed'})

        # Re-vérifier côté PlopPlop — ne jamais faire confiance au payload seul
        svc    = PlopPlopService()
        result = svc.verify_payment(reference_id)

        if result['success'] and result['paid']:
            process_successful_payment(
                transaction,
                external_id=result.get('id_transaction', ''),
                method=result.get('method', ''),
            )
            return JsonResponse({'status': 'ok'})

        return JsonResponse({'status': 'not_paid'}, status=400)
