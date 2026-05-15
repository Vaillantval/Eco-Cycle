from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<slug:slug>/enroll/', views.EnrollView.as_view(), name='course_enroll'),
    path('lessons/<uuid:pk>/complete/', views.CompleteLessonView.as_view(), name='lesson_complete'),
    path('my-enrollments/', views.MyEnrollmentsView.as_view(), name='my_enrollments'),
    path('my-certificates/', views.MyCertificatesView.as_view(), name='my_certificates'),
]
