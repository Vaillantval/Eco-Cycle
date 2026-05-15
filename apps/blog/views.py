from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Post
from .serializers import PostListSerializer, PostDetailSerializer


class PostListView(generics.ListAPIView):
    """GET /api/blog/posts/"""
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Post.objects.filter(
        status='published'
    ).select_related('author', 'category').order_by('-published_at')
    filterset_fields = ['category']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'views', 'read_time_minutes']


class PostDetailView(generics.RetrieveAPIView):
    """GET /api/blog/posts/<slug>/"""
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Post.objects.filter(status='published').select_related('author', 'category')
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Post.objects.filter(pk=instance.pk).update(views=instance.views + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
