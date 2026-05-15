from django.urls import path
from . import views

urlpatterns = [
    path('subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('confirm/<uuid:token>/', views.NewsletterConfirmView.as_view(), name='newsletter_confirm'),
]
