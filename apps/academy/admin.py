from django.contrib import admin
from .models import Course, Lesson, LessonVideo, Enrollment, Certificate


class LessonVideoInline(admin.TabularInline):
    model = LessonVideo
    extra = 0
    fields = ['title', 'order', 'duration_minutes', 'video_file', 'video_url', 'allow_download']
    ordering = ['order']


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ['title', 'order', 'duration_minutes']
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'duration_minutes', 'is_published', 'is_free', 'created_at']
    list_filter = ['level', 'is_published', 'is_free']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['id', 'created_at']
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration_minutes', 'pdf_allow_download']
    list_filter = ['course', 'pdf_allow_download']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']
    fieldsets = [
        (None, {'fields': ['course', 'title', 'order', 'content']}),
        ('PDF', {'fields': ['pdf_file', 'pdf_allow_download']}),
    ]
    inlines = [LessonVideoInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'progress_percent', 'is_completed', 'enrolled_at']
    list_filter = ['is_completed', 'course']
    search_fields = ['user__email', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'issued_at']
    search_fields = ['user__email', 'course__title']
    readonly_fields = ['id', 'issued_at']
