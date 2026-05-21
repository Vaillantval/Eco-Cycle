from django.urls import path
from . import admin_views

urlpatterns = [
    path('stats/',              admin_views.AdminStatsView.as_view(),       name='admin_stats'),
    path('users/',              admin_views.AdminUserListView.as_view(),     name='admin_users'),
    path('users/<uuid:pk>/',   admin_views.AdminUserDetailView.as_view(),   name='admin_user_detail'),
    path('collectors/',         admin_views.AdminCollectorListView.as_view(), name='admin_collectors'),
]
