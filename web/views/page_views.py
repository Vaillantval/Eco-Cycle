from django.db.models import Sum
from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from apps.core.serializers import ContactMessageSerializer
from apps.impact.models import ImpactRecord


class CommentCaMarcheView(TemplateView):
    template_name = 'pages/comment_ca_marche.html'


class FonctionnalitesView(TemplateView):
    template_name = 'pages/fonctionnalites.html'


class NotreImpactView(View):
    def get(self, request):
        from apps.accounts.models import User
        from apps.collections.models import PickupRequest
        stats = {
            'total_users': User.objects.filter(is_active=True).count(),
            'total_kg_recycled': ImpactRecord.objects.aggregate(t=Sum('kg_recycled'))['t'] or 0,
            'total_collections': PickupRequest.objects.filter(status='completed').count(),
            'total_co2_saved': ImpactRecord.objects.aggregate(t=Sum('co2_saved_kg'))['t'] or 0,
        }
        return render(request, 'pages/notre_impact.html', {'stats': stats})


class FaqView(TemplateView):
    template_name = 'pages/faq.html'


class ContactPageView(View):
    def get(self, request):
        return render(request, 'pages/contact.html')

    def post(self, request):
        data = request.POST.dict()
        data.pop('csrfmiddlewaretoken', None)
        serializer = ContactMessageSerializer(data=data)
        if not serializer.is_valid():
            messages.error(request, 'Erreur dans le formulaire. Vérifiez vos données.')
            return render(request, 'pages/contact.html')

        message = serializer.save()

        try:
            from apps.notifications.tasks import notify_contact_message
            notify_contact_message.delay(message.id)
        except Exception:
            pass

        messages.success(request, 'Message envoyé ! Nous vous répondrons bientôt.')
        return redirect('contact')
