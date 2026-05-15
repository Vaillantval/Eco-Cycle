from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from apps.blog.models import Post, BlogCategory


class BlogListView(View):
    def get(self, request):
        category_slug = request.GET.get('category', '')
        posts = Post.objects.filter(status='published').select_related('author', 'category').order_by('-published_at')
        categories = BlogCategory.objects.all()
        active_category = None

        if category_slug:
            active_category = BlogCategory.objects.filter(slug=category_slug).first()
            if active_category:
                posts = posts.filter(category=active_category)

        return render(request, 'blog/list.html', {
            'posts': posts,
            'categories': categories,
            'active_category': active_category,
        })


class BlogDetailView(View):
    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status='published')
        post.views += 1
        post.save(update_fields=['views'])

        related = Post.objects.filter(
            status='published', category=post.category
        ).exclude(pk=post.pk).order_by('-published_at')[:3]

        return render(request, 'blog/detail.html', {
            'post': post,
            'related': related,
        })
