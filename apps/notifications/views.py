from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/"""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    """POST /api/notifications/<id>/read/"""
    def post(self, request, pk):
        notif = Notification.objects.filter(pk=pk, user=request.user).first()
        if notif:
            notif.is_read = True
            notif.save()
        return Response({'status': 'ok'})


class MarkAllReadView(APIView):
    """POST /api/notifications/read-all/"""
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'ok'})


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
