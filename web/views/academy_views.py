from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.mixins import LoginRequiredMixin
from apps.academy.models import Course, Lesson, Enrollment


class AcademyListView(View):
    def get(self, request):
        level_filter = request.GET.get('level', '')
        courses = Course.objects.filter(is_published=True).prefetch_related('lessons').order_by('created_at')
        if level_filter:
            courses = courses.filter(level=level_filter)

        user_enrollments = {}
        if request.session.get('user_id'):
            from apps.accounts.models import User
            try:
                user = User.objects.get(id=request.session['user_id'])
                for e in Enrollment.objects.filter(user=user).select_related('course'):
                    user_enrollments[str(e.course_id)] = e
            except User.DoesNotExist:
                pass

        return render(request, 'academy/list.html', {
            'courses': courses,
            'level_filter': level_filter,
            'level_choices': Course.LEVEL_CHOICES,
            'user_enrollments': user_enrollments,
        })


class CourseDetailView(View):
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        lessons = course.lessons.all()
        enrollment = None
        completed_ids = set()

        if request.session.get('user_id'):
            from apps.accounts.models import User
            try:
                user = User.objects.get(id=request.session['user_id'])
                enrollment = Enrollment.objects.filter(user=user, course=course).first()
                if enrollment:
                    completed_ids = set(str(l.id) for l in enrollment.completed_lessons.all())
            except User.DoesNotExist:
                pass

        return render(request, 'academy/detail.html', {
            'course': course,
            'lessons': lessons,
            'enrollment': enrollment,
            'completed_ids': completed_ids,
            'total_lessons': lessons.count(),
        })


class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, slug):
        user = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)
        _, created = Enrollment.objects.get_or_create(user=user, course=course)
        if created:
            messages.success(request, f'Inscrit au cours « {course.title} » !')
        else:
            messages.info(request, 'Vous êtes déjà inscrit à ce cours.')
        return redirect('course_detail', slug=slug)


class CompleteLessonView(LoginRequiredMixin, View):
    def post(self, request, slug, lesson_id):
        user = self.get_current_user(request)
        course = get_object_or_404(Course, slug=slug, is_published=True)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        enrollment = get_object_or_404(Enrollment, user=user, course=course)

        enrollment.completed_lessons.add(lesson)
        enrollment.update_progress()

        if enrollment.is_completed:
            messages.success(request, f'Félicitations ! Cours « {course.title} » terminé !')
        return redirect('course_detail', slug=slug)
