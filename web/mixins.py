from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.models import User


class LoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'Connectez-vous pour accéder à cette page.')
            return redirect('web_login')
        return super().dispatch(request, *args, **kwargs)

    def get_current_user(self, request):
        try:
            return User.objects.get(id=request.session['user_id'])
        except User.DoesNotExist:
            return None


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if hasattr(result, 'status_code') and result.status_code in (301, 302):
            return result
        if request.session.get('user_role') != 'admin':
            messages.error(request, 'Accès réservé aux administrateurs.')
            return redirect('dashboard')
        return result


class CollectorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if hasattr(result, 'status_code') and result.status_code in (301, 302):
            return result
        if request.session.get('user_role') not in ['collector', 'admin']:
            messages.error(request, 'Accès réservé aux collecteurs.')
            return redirect('dashboard')
        return result
