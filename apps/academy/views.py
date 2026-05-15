from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Course, Lesson, Enrollment, Certificate
from .serializers import (
    CourseListSerializer, CourseDetailSerializer,
    EnrollmentSerializer, CertificateSerializer,
)
from apps.accounts.permissions import IsAdmin


class CourseListView(generics.ListAPIView):
    """GET /api/academy/courses/"""
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Course.objects.filter(is_published=True)
    filterset_fields = ['level', 'is_free']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'duration_minutes']


class CourseDetailView(generics.RetrieveAPIView):
    """GET /api/academy/courses/<slug>/"""
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Course.objects.filter(is_published=True).prefetch_related('lessons')
    lookup_field = 'slug'


class EnrollView(APIView):
    """POST /api/academy/courses/<slug>/enroll/"""
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user, course=course
        )
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CompleteLessonView(APIView):
    """POST /api/academy/lessons/<id>/complete/"""
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        enrollment = get_object_or_404(
            Enrollment, user=request.user, course=lesson.course
        )
        enrollment.completed_lessons.add(lesson)
        enrollment.update_progress()

        if enrollment.is_completed:
            Certificate.objects.get_or_create(user=request.user, course=lesson.course)

        return Response(EnrollmentSerializer(enrollment).data)


class MyEnrollmentsView(generics.ListAPIView):
    """GET /api/academy/my-enrollments/"""
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user
        ).select_related('course').prefetch_related('completed_lessons')


class MyCertificatesView(generics.ListAPIView):
    """GET /api/academy/my-certificates/"""
    serializer_class = CertificateSerializer

    def get_queryset(self):
        return Certificate.objects.filter(
            user=self.request.user
        ).select_related('course')
