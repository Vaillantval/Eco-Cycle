from rest_framework import serializers
from .models import Course, Lesson, LessonVideo, Enrollment, Certificate


# ─────────────────────────────────────────────────────────
#  Vidéos
# ─────────────────────────────────────────────────────────

class LessonVideoSerializer(serializers.ModelSerializer):
    embed_url = serializers.SerializerMethodField()
    platform  = serializers.SerializerMethodField()

    class Meta:
        model  = LessonVideo
        fields = [
            'id', 'title', 'video_file', 'video_url', 'embed_url',
            'platform', 'allow_download', 'duration_minutes', 'order',
        ]
        read_only_fields = ['id']

    def get_embed_url(self, obj):
        return obj.embed_url()

    def get_platform(self, obj):
        if obj.is_youtube():   return 'youtube'
        if obj.is_vimeo():     return 'vimeo'
        if obj.is_tiktok():    return 'tiktok'
        if obj.is_instagram(): return 'instagram'
        if obj.video_file:     return 'direct'
        return 'unknown'


# ─────────────────────────────────────────────────────────
#  Leçons (lecture publique)
# ─────────────────────────────────────────────────────────

class LessonSerializer(serializers.ModelSerializer):
    videos = LessonVideoSerializer(many=True, read_only=True)

    class Meta:
        model  = Lesson
        fields = [
            'id', 'title', 'content',
            'pdf_display_mode', 'pdf_allow_download',
            'order', 'duration_minutes',
            'videos',
        ]


# ─────────────────────────────────────────────────────────
#  Cours (lecture publique)
# ─────────────────────────────────────────────────────────

class CourseListSerializer(serializers.ModelSerializer):
    lesson_count     = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    level_display    = serializers.ReadOnlyField(source='get_level_display')

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'slug', 'description', 'thumbnail',
            'level', 'level_display', 'duration_minutes', 'price',
            'is_free', 'lesson_count', 'enrollment_count', 'created_at',
        ]

    def get_lesson_count(self, obj):
        return obj.lessons.count()

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class CourseDetailSerializer(CourseListSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['lessons', 'auto_advance_delay']


# ─────────────────────────────────────────────────────────
#  Enrollments / Certificats
# ─────────────────────────────────────────────────────────

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title       = serializers.ReadOnlyField(source='course.title')
    course_slug        = serializers.ReadOnlyField(source='course.slug')
    completed_lesson_ids = serializers.SerializerMethodField()

    class Meta:
        model  = Enrollment
        fields = [
            'id', 'course', 'course_title', 'course_slug',
            'progress_percent', 'is_completed', 'payment_status',
            'completed_lesson_ids', 'enrolled_at', 'completed_at',
        ]

    def get_completed_lesson_ids(self, obj):
        return list(obj.completed_lessons.values_list('id', flat=True))


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.ReadOnlyField(source='course.title')
    course_slug  = serializers.ReadOnlyField(source='course.slug')
    user_name    = serializers.ReadOnlyField(source='user.full_name')

    class Meta:
        model  = Certificate
        fields = ['id', 'course', 'course_title', 'course_slug', 'user_name', 'issued_at']


# ─────────────────────────────────────────────────────────
#  Admin — Cours
# ─────────────────────────────────────────────────────────

class AdminCourseSerializer(serializers.ModelSerializer):
    lesson_count     = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    level_display    = serializers.ReadOnlyField(source='get_level_display')

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'slug', 'description', 'thumbnail',
            'level', 'level_display', 'price', 'is_published',
            'duration_minutes', 'auto_advance_delay',
            'lesson_count', 'enrollment_count', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'duration_minutes', 'created_at',
                            'level_display', 'lesson_count', 'enrollment_count']

    def get_lesson_count(self, obj):
        return obj.lessons.count()

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


# ─────────────────────────────────────────────────────────
#  Admin — Leçons
# ─────────────────────────────────────────────────────────

class AdminLessonSerializer(serializers.ModelSerializer):
    videos = LessonVideoSerializer(many=True, read_only=True)

    class Meta:
        model  = Lesson
        fields = [
            'id', 'course', 'title', 'content',
            'pdf_file', 'pdf_display_mode', 'pdf_allow_download',
            'order', 'duration_minutes', 'pdf_reading_minutes',
            'videos',
        ]
        read_only_fields = ['id', 'duration_minutes', 'pdf_reading_minutes', 'videos']


# ─────────────────────────────────────────────────────────
#  Admin — Vidéos
# ─────────────────────────────────────────────────────────

class AdminLessonVideoSerializer(serializers.ModelSerializer):
    embed_url = serializers.SerializerMethodField()
    platform  = serializers.SerializerMethodField()

    class Meta:
        model  = LessonVideo
        fields = [
            'id', 'lesson', 'title', 'video_file', 'video_url',
            'embed_url', 'platform', 'allow_download', 'duration_minutes', 'order',
        ]
        read_only_fields = ['id', 'embed_url', 'platform']

    def get_embed_url(self, obj):
        return obj.embed_url()

    def get_platform(self, obj):
        if obj.is_youtube():   return 'youtube'
        if obj.is_vimeo():     return 'vimeo'
        if obj.is_tiktok():    return 'tiktok'
        if obj.is_instagram(): return 'instagram'
        if obj.video_file:     return 'direct'
        return 'unknown'
