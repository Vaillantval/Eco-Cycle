from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from .models import ContactMessage, NewsletterSubscriber
from .serializers import ContactMessageSerializer, NewsletterSerializer


class ContactView(APIView):
    """POST /api/contact/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        from apps.notifications.email_service import EmailService
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            EmailService._send(
                admin.email,
                f'[EcoCycle Contact] {message.subject}',
                f'<p>De : {message.first_name} {message.last_name} ({message.email})</p>'
                f'<p>{message.message}</p>',
            )
        return Response({'message': 'Message envoyé avec succès.'}, status=status.HTTP_201_CREATED)


class NewsletterSubscribeView(APIView):
    """POST /api/newsletter/subscribe/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = NewsletterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created or not subscriber.is_confirmed:
            from apps.notifications.email_service import EmailService
            EmailService.send_newsletter_confirmation(subscriber)
        return Response({'message': "Vérifiez votre email pour confirmer l'abonnement."})


class NewsletterConfirmView(APIView):
    """GET /api/newsletter/confirm/<token>/"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        subscriber = get_object_or_404(NewsletterSubscriber, token=token)
        subscriber.is_confirmed = True
        subscriber.save()
        return Response({'message': 'Abonnement confirmé !'})
