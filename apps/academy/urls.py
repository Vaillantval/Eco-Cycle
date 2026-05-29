from django.urls import path
from . import views

urlpatterns = [
    # ── Public / User ─────────────────────────────────────
    path('courses/',                        views.CourseListView.as_view(),        name='course_list'),
    path('courses/<slug:slug>/',            views.CourseDetailView.as_view()),
    path('courses/<slug:slug>/enroll/',     views.EnrollView.as_view(),            name='course_enroll'),
    path('courses/<slug:slug>/quiz/',       views.CourseQuizView.as_view(),        name='course_quiz'),
    path('lessons/<uuid:pk>/complete/',     views.CompleteLessonView.as_view(),    name='lesson_complete'),
    path('my-enrollments/',                 views.MyEnrollmentsView.as_view(),     name='my_enrollments'),
    path('my-certificates/',               views.MyCertificatesView.as_view(),    name='api_my_certificates'),

    # ── Paiement cours (API JWT — Flutter) ────────────────
    path('courses/<slug:slug>/pay/stripe/init/',
         views.CourseStripeInitAPIView.as_view(),    name='course_stripe_init'),
    path('courses/<slug:slug>/pay/stripe/confirm/',
         views.CourseStripeConfirmAPIView.as_view(), name='course_stripe_confirm'),
    path('courses/<slug:slug>/pay/plopplop/',
         views.CoursePlopPlopInitAPIView.as_view(),  name='course_plopplop_init'),
    path('courses/<slug:slug>/pay/plopplop/retour/',
         views.CoursePlopPlopRetourAPIView.as_view(), name='course_plopplop_retour'),

    # ── Admin — CRUD Cours ────────────────────────────────
    path('admin/courses/',               views.AdminCourseListCreateView.as_view(), name='admin_course_list'),
    path('admin/courses/<slug:slug>/',   views.AdminCourseDetailView.as_view(),     name='admin_course_detail'),

    # ── Admin — CRUD Leçons ───────────────────────────────
    path('admin/lessons/',               views.AdminLessonListCreateView.as_view(), name='admin_lesson_list'),
    path('admin/lessons/<uuid:pk>/',     views.AdminLessonDetailView.as_view(),     name='admin_lesson_detail'),

    # ── Admin — Vidéos ────────────────────────────────────
    path('admin/lessons/<uuid:pk>/videos/', views.AdminLessonVideoCreateView.as_view(), name='admin_video_create'),
    path('admin/videos/<uuid:pk>/',          views.AdminVideoDeleteView.as_view(),        name='admin_video_delete'),
]
