from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, FCMTokenSerializer,
    ResetPasswordRequestSerializer, ResetPasswordConfirmSerializer,
)
from .tasks import send_verification_email, send_password_reset_email


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email.delay(str(user.id))
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Compte créé. Vérifiez votre email.',
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """GET /api/auth/verify-email/<token>/"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        verification = get_object_or_404(EmailVerificationToken, token=token)
        if not verification.is_valid():
            return Response({'error': 'Token expiré.'}, status=status.HTTP_400_BAD_REQUEST)
        verification.user.is_email_verified = True
        verification.user.save()
        verification.delete()
        return Response({'message': 'Email vérifié avec succès.'})


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'error': 'Identifiants invalides.'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
        })


class LogoutView(APIView):
    """POST /api/auth/logout/"""
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Déconnexion réussie.'})
        except Exception:
            return Response({'error': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/auth/profile/"""
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateProfileSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = self.request.user
        old_address = user.address
        old_city    = user.city
        serializer.save()
        if user.address != old_address or user.city != old_city:
            try:
                from .tasks import geocode_user_location
                geocode_user_location.delay(str(user.id))
            except Exception:
                pass


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Mot de passe modifié.'})


class UpdateFCMTokenView(APIView):
    """POST /api/auth/fcm-token/"""
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data['fcm_token']
        request.user.save()
        return Response({'message': 'Token FCM mis à jour.'})


class ResetPasswordRequestView(APIView):
    """POST /api/auth/reset-password/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(str(user.id))
        except User.DoesNotExist:
            pass
        return Response({'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'})


class ResetPasswordConfirmView(APIView):
    """POST /api/auth/reset-password/confirm/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_token = get_object_or_404(PasswordResetToken, token=serializer.validated_data['token'])
        if not reset_token.is_valid():
            return Response({'error': 'Token expiré ou déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)
        reset_token.user.set_password(serializer.validated_data['new_password'])
        reset_token.user.save()
        reset_token.used = True
        reset_token.save()
        return Response({'message': 'Mot de passe réinitialisé.'})
