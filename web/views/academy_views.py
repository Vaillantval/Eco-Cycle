from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.mixins import LoginRequiredMixin
from apps.academy.models import Course, Lesson, LessonVideo, Enrollment, Certificate


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

        lessons_list = list(lessons)
        return render(request, 'academy/detail.html', {
            'course': course,
            'lessons': lessons_list,
            'enrollment': enrollment,
            'completed_ids': completed_ids,
            'total_lessons': len(lessons_list),
            'first_lesson': lessons_list[0] if lessons_list else None,
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
            cert, created = Certificate.objects.get_or_create(user=user, course=course)
            if created:
                from apps.notifications.tasks import notify_course_completed
                notify_course_completed.delay(str(user.id), str(course.id), str(cert.id))
            messages.success(request, f'Félicitations ! Cours « {course.title} » terminé ! Votre certificat est disponible.')
        return redirect('lesson_detail', slug=slug, lesson_id=lesson_id)


class LessonDetailView(LoginRequiredMixin, View):
    def get(self, request, slug, lesson_id):
        user = self.get_current_user(request)
        course = get_object_or_404(
            Course.objects.prefetch_related('lessons__videos'),
            slug=slug, is_published=True,
        )
        enrollment = get_object_or_404(
            Enrollment.objects.prefetch_related('completed_lessons'),
            user=user, course=course,
        )
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

        lessons = list(course.lessons.all())  # already prefetched, no extra query
        idx = next((i for i, l in enumerate(lessons) if str(l.id) == str(lesson.id)), 0)
        prev_lesson = lessons[idx - 1] if idx > 0 else None
        next_lesson = lessons[idx + 1] if idx < len(lessons) - 1 else None

        completed_ids = set(str(l.id) for l in enrollment.completed_lessons.all())  # prefetched
        is_done = str(lesson.id) in completed_ids
        videos = [v for v in lesson.videos.all() if True]  # prefetched via lessons__videos

        return render(request, 'academy/lesson_detail.html', {
            'course': course,
            'lesson': lesson,
            'lessons': lessons,
            'videos': videos,
            'enrollment': enrollment,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
            'is_done': is_done,
            'completed_ids': completed_ids,
        })
