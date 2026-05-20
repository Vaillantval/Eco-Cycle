from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from apps.accounts.models import User, EmailVerificationToken, PasswordResetToken
from apps.accounts.tasks import send_verification_email, send_password_reset_email
from web.mixins import LoginRequiredMixin


class WebLoginView(View):
    template_name = 'auth/login.html'

    def get(self, request):
        if request.session.get('user_id'):
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if not user:
            return render(request, self.template_name, {
                'error': 'Email ou mot de passe incorrect.',
                'email': email,
            })
        if not user.is_active:
            return render(request, self.template_name, {
                'error': 'Ce compte est désactivé.',
                'email': email,
            })

        request.session['user_id']    = str(user.id)
        request.session['user_role']  = user.role
        request.session['user_name']  = user.full_name
        request.session['user_email'] = user.email

        messages.success(request, f'Bienvenue, {user.first_name} !')

        next_url = request.GET.get('next', '')
        if next_url:
            return redirect(next_url)
        if user.role == 'admin':
            return redirect('admin_panel')
        if user.role == 'collector':
            return redirect('collector_dashboard')
        return redirect('dashboard')


class WebRegisterView(View):
    template_name = 'auth/register.html'

    def get(self, request):
        if request.session.get('user_id'):
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        data = request.POST
        errors = {}

        if not data.get('first_name'):
            errors['first_name'] = 'Prénom requis.'
        if not data.get('last_name'):
            errors['last_name'] = 'Nom requis.'
        if not data.get('email'):
            errors['email'] = 'Email requis.'
        elif User.objects.filter(email=data['email']).exists():
            errors['email'] = 'Cet email est déjà utilisé.'
        if not data.get('password') or len(data.get('password', '')) < 8:
            errors['password'] = 'Mot de passe : 8 caractères minimum.'
        if data.get('password') != data.get('password_confirm'):
            errors['password_confirm'] = 'Les mots de passe ne correspondent pas.'

        if errors:
            return render(request, self.template_name, {'errors': errors, 'data': data})

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
        )
        send_verification_email.delay(str(user.id))
        from apps.notifications.tasks import notify_admin_new_user
        notify_admin_new_user.delay(str(user.id))

        messages.success(request, 'Compte créé ! Vérifiez votre email pour activer votre compte.')
        return redirect('web_login')


class WebLogoutView(LoginRequiredMixin, View):
    def get(self, request):
        request.session.flush()
        messages.info(request, 'Vous êtes déconnecté.')
        return redirect('home')


class VerifyEmailWebView(View):
    def get(self, request, token):
        try:
            verification = EmailVerificationToken.objects.get(token=token)
            if not verification.is_valid():
                messages.error(request, 'Ce lien de vérification a expiré.')
                return redirect('web_login')
            verification.user.is_email_verified = True
            verification.user.save()
            verification.delete()
            messages.success(request, 'Email vérifié ! Vous pouvez maintenant vous connecter.')
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, 'Lien de vérification invalide.')
        return redirect('web_login')


class ResetPasswordWebView(View):
    template_name = 'auth/reset_password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(str(user.id))
        except User.DoesNotExist:
            pass
        messages.info(request, 'Si cet email existe, un lien de réinitialisation a été envoyé.')
        return redirect('web_login')


class ResetPasswordConfirmWebView(View):
    template_name = 'auth/reset_password_confirm.html'

    def get(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, 'Ce lien a expiré. Demandez un nouveau lien.')
                return redirect('reset_password')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Lien invalide.')
            return redirect('reset_password')
        return render(request, self.template_name, {'token': token})

    def post(self, request, token):
        password = request.POST.get('new_password', '')
        confirm  = request.POST.get('password_confirm', '')
        if password != confirm or len(password) < 8:
            return render(request, self.template_name, {
                'token': token,
                'error': 'Mots de passe invalides (8 caractères minimum, doivent correspondre).',
            })
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, 'Ce lien a expiré.')
                return redirect('reset_password')
            reset_token.user.set_password(password)
            reset_token.user.save()
            reset_token.used = True
            reset_token.save()
            messages.success(request, 'Mot de passe réinitialisé avec succès. Connectez-vous.')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Token invalide.')
        return redirect('web_login')
