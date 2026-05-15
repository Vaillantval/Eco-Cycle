from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.MyImpactDashboardView.as_view(), name='impact_dashboard'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='impact_leaderboard'),
    path('stats/', views.PublicStatsView.as_view(), name='impact_stats'),
]
