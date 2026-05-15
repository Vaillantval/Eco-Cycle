from rest_framework import serializers
from .models import Course, Lesson, Enrollment, Certificate


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'video_url', 'order', 'duration_minutes']


class CourseListSerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    level_display = serializers.ReadOnlyField(source='get_level_display')

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'thumbnail',
            'level', 'level_display', 'duration_minutes',
            'is_free', 'lesson_count', 'enrollment_count', 'created_at',
        ]

    def get_lesson_count(self, obj):
        return obj.lessons.count()

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class CourseDetailSerializer(CourseListSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['lessons']


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.ReadOnlyField(source='course.title')
    course_slug = serializers.ReadOnlyField(source='course.slug')
    completed_lesson_ids = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_title', 'course_slug',
            'progress_percent', 'is_completed',
            'completed_lesson_ids', 'enrolled_at', 'completed_at',
        ]

    def get_completed_lesson_ids(self, obj):
        return list(obj.completed_lessons.values_list('id', flat=True))


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.ReadOnlyField(source='course.title')
    course_slug = serializers.ReadOnlyField(source='course.slug')
    user_name = serializers.ReadOnlyField(source='user.full_name')

    class Meta:
        model = Certificate
        fields = ['id', 'course', 'course_title', 'course_slug', 'user_name', 'issued_at']
