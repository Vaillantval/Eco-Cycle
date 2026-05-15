from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('profile/', views.ProfileView.as_view()),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('fcm-token/', views.UpdateFCMTokenView.as_view(), name='fcm_token'),
    path('reset-password/', views.ResetPasswordRequestView.as_view(), name='reset_password_request'),
    path('reset-password/confirm/', views.ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
]
