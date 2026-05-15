from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('unread-count/', views.UnreadCountView.as_view(), name='notification_unread_count'),
    path('read-all/', views.MarkAllReadView.as_view(), name='notification_read_all'),
    path('<uuid:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification_read'),
]
