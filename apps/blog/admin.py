from django.contrib import admin
from .models import BlogCategory, Post


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'views', 'published_at', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['title', 'excerpt', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['id', 'views', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Article', {'fields': ('id', 'author', 'category', 'title', 'slug')}),
        ('Contenu', {'fields': ('excerpt', 'content', 'cover_image')}),
        ('Publication', {'fields': ('status', 'published_at', 'read_time_minutes')}),
        ('Stats', {'fields': ('views', 'created_at', 'updated_at')}),
    )
