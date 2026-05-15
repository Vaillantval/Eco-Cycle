from rest_framework import serializers
from .models import BlogCategory, Post


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'slug']


class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.full_name')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'cover_image',
            'author_name', 'category', 'category_name',
            'read_time_minutes', 'views', 'published_at',
        ]


class PostDetailSerializer(PostListSerializer):
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['content', 'created_at', 'updated_at']
