from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import ContactMessage, NewsletterSubscriber
from .serializers import ContactMessageSerializer, NewsletterSerializer


def _is_html_request(request):
    return 'application/x-www-form-urlencoded' in request.content_type or \
           'multipart/form-data' in request.content_type


class ContactView(APIView):
    """POST /api/contact/ ou /contact/ (web form)"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            if _is_html_request(request):
                messages.error(request, 'Erreur dans le formulaire. Vérifiez vos données.')
                return redirect('home')
            serializer.is_valid(raise_exception=True)

        message = serializer.save()

        try:
            from apps.notifications.tasks import notify_contact_message
            notify_contact_message.delay(message.id)
        except Exception:
            pass

        if _is_html_request(request):
            messages.success(request, 'Message envoyé avec succès ! Nous vous répondrons bientôt.')
            return redirect('home')
        return Response({'message': 'Message envoyé avec succès.'}, status=status.HTTP_201_CREATED)


class NewsletterSubscribeView(APIView):
    """POST /api/newsletter/subscribe/ ou /newsletter/subscribe/ (web form)"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = NewsletterSerializer(data=request.data)
        if not serializer.is_valid():
            if _is_html_request(request):
                messages.error(request, 'Adresse email invalide.')
                return redirect('home')
            serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created or not subscriber.is_confirmed:
            try:
                from apps.notifications.tasks import notify_newsletter_signup
                notify_newsletter_signup.delay(subscriber.id)
            except Exception:
                pass

        if _is_html_request(request):
            messages.success(request, "Inscription enregistrée ! Vérifiez votre email pour confirmer.")
            return redirect('home')
        return Response({'message': "Vérifiez votre email pour confirmer l'abonnement."})


class NewsletterConfirmView(APIView):
    """GET /api/newsletter/confirm/<token>/ ou /newsletter/confirm/<token>/"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        subscriber = get_object_or_404(NewsletterSubscriber, token=token)
        subscriber.is_confirmed = True
        subscriber.save()
        if 'text/html' in request.META.get('HTTP_ACCEPT', ''):
            messages.success(request, 'Abonnement confirmé ! Bienvenue dans la communauté EcoCycle.')
            return redirect('home')
        return Response({'message': 'Abonnement confirmé !'})
