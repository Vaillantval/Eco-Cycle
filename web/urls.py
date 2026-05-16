from django.urls import path
from django.views.generic import TemplateView
from .views import HomeView
from .views.auth_views import (
    WebLoginView, WebRegisterView, WebLogoutView,
    VerifyEmailWebView, ResetPasswordWebView, ResetPasswordConfirmWebView,
)
from .views.dashboard_views import (
    DashboardOverviewView, MyListingsView, SubmitWasteView,
    MyOrdersView, MyImpactView, MyCertificatesView, ProfileView,
)
from .views.marketplace_views import (
    MarketplaceListView, AuctionDetailView, PlaceBidWebView, BuyNowWebView,
)
from .views.collection_views import MyPickupsView, RequestPickupView, PickupDetailView
from .views.admin_views import (
    AdminDashboardView, AdminListingsView, AdminReviewListingView,
    AdminPickupsView, AdminUsersView, AdminOrdersView,
    AdminUserDetailView, AdminPickupDetailView, AdminOrderDetailView,
    AdminBlogView, AdminBlogCreateView, AdminBlogEditView, AdminBlogCategoriesView,
    AdminAcademyView, AdminAcademyCourseCreateView, AdminAcademyCourseDetailView,
    AdminAcademyLessonCreateView, AdminAcademyLessonEditView,
    AdminAcademyEnrollmentsView, AdminAcademyCertificatesView,
    AdminNewslettersView, AdminContactsView, AdminSiteConfigView,
    AdminSlidersView, AdminCertificatePDFView, CertificatePDFView,
)
from .views.collector_views import (
    CollectorDashboardView, CollectorPickupsView,
    CollectorPickupDetailView, CollectorProfileView,
)
from .views.blog_views import BlogListView, BlogDetailView
from .views.academy_views import AcademyListView, CourseDetailView, EnrollCourseView, CompleteLessonView
from apps.core.views import NewsletterSubscribeView, NewsletterConfirmView
from .views.page_views import (
    CommentCaMarcheView, FonctionnalitesView, NotreImpactView,
    FaqView, ContactPageView,
)

urlpatterns = [
    # Landing
    path('', HomeView.as_view(), name='home'),

    # Pages dédiées (La Plateforme + Apprendre)
    path('comment-ca-marche/', CommentCaMarcheView.as_view(), name='comment_ca_marche'),
    path('fonctionnalites/',   FonctionnalitesView.as_view(), name='fonctionnalites'),
    path('notre-impact/',      NotreImpactView.as_view(),     name='notre_impact'),
    path('faq/',               FaqView.as_view(),             name='faq'),

    # Auth
    path('login/',    WebLoginView.as_view(),    name='web_login'),
    path('register/', WebRegisterView.as_view(), name='web_register'),
    path('logout/',   WebLogoutView.as_view(),   name='web_logout'),
    path('verify-email/<uuid:token>/',
         VerifyEmailWebView.as_view(), name='verify_email_web'),
    path('reset-password/',
         ResetPasswordWebView.as_view(), name='reset_password'),
    path('reset-password/confirm/<uuid:token>/',
         ResetPasswordConfirmWebView.as_view(), name='reset_password_confirm_web'),

    # Dashboard
    path('dashboard/',
         DashboardOverviewView.as_view(), name='dashboard'),
    path('dashboard/listings/',
         MyListingsView.as_view(), name='my_listings'),
    path('dashboard/listings/submit/',
         SubmitWasteView.as_view(), name='submit_waste'),
    path('dashboard/orders/',
         MyOrdersView.as_view(), name='my_orders'),
    path('dashboard/impact/',
         MyImpactView.as_view(), name='my_impact'),
    path('dashboard/certificates/',
         MyCertificatesView.as_view(), name='my_certificates'),
    path('dashboard/certificates/<uuid:cert_id>/pdf/',
         CertificatePDFView.as_view(), name='certificate_pdf'),
    path('dashboard/profile/',
         ProfileView.as_view(), name='profile'),

    # Contact & newsletter
    path('contact/', ContactPageView.as_view(), name='contact'),
    path('newsletter/subscribe/',
         NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('newsletter/confirm/<uuid:token>/',
         NewsletterConfirmView.as_view(), name='newsletter_confirm'),

    # Marketplace W5
    path('marketplace/',
         MarketplaceListView.as_view(), name='marketplace'),
    path('marketplace/<uuid:pk>/',
         AuctionDetailView.as_view(), name='auction_detail'),
    path('marketplace/<uuid:pk>/bid/',
         PlaceBidWebView.as_view(), name='place_bid'),
    path('marketplace/<uuid:pk>/buy-now/',
         BuyNowWebView.as_view(), name='buy_now'),
    # Blog W8
    path('blog/',
         BlogListView.as_view(), name='blog_list'),
    path('blog/<slug:slug>/',
         BlogDetailView.as_view(), name='blog_detail'),

    # Academy W8
    path('academy/',
         AcademyListView.as_view(), name='academy_list'),
    path('academy/<slug:slug>/',
         CourseDetailView.as_view(), name='course_detail'),
    path('academy/<slug:slug>/enroll/',
         EnrollCourseView.as_view(), name='enroll_course'),
    path('academy/<slug:slug>/lessons/<uuid:lesson_id>/complete/',
         CompleteLessonView.as_view(), name='complete_lesson'),
    path('dashboard/pickups/',
         MyPickupsView.as_view(), name='my_pickups'),
    path('dashboard/pickups/request/',
         RequestPickupView.as_view(), name='request_pickup'),
    path('dashboard/pickups/<uuid:pk>/',
         PickupDetailView.as_view(), name='pickup_detail'),
    # Collector Dashboard
    path('collector/',
         CollectorDashboardView.as_view(), name='collector_dashboard'),
    path('collector/pickups/',
         CollectorPickupsView.as_view(), name='web_collector_pickups'),
    path('collector/pickups/<uuid:pk>/',
         CollectorPickupDetailView.as_view(), name='collector_pickup_detail'),
    path('collector/profile/',
         CollectorProfileView.as_view(), name='collector_profile'),

    # Admin Panel
    path('panel/',
         AdminDashboardView.as_view(), name='admin_panel'),
    path('panel/listings/',
         AdminListingsView.as_view(), name='admin_listings'),
    path('panel/listings/<uuid:pk>/',
         AdminReviewListingView.as_view(), name='admin_review_listing'),
    path('panel/pickups/',
         AdminPickupsView.as_view(), name='admin_pickups'),
    path('panel/pickups/<uuid:pk>/',
         AdminPickupDetailView.as_view(), name='admin_pickup_detail'),
    path('panel/users/',
         AdminUsersView.as_view(), name='admin_users'),
    path('panel/users/<uuid:pk>/',
         AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('panel/orders/',
         AdminOrdersView.as_view(), name='admin_orders'),
    path('panel/orders/<uuid:pk>/',
         AdminOrderDetailView.as_view(), name='admin_order_detail'),
    # Blog
    path('panel/blog/',
         AdminBlogView.as_view(), name='admin_blog'),
    path('panel/blog/create/',
         AdminBlogCreateView.as_view(), name='admin_blog_create'),
    path('panel/blog/<uuid:pk>/edit/',
         AdminBlogEditView.as_view(), name='admin_blog_edit'),
    path('panel/blog/categories/',
         AdminBlogCategoriesView.as_view(), name='admin_blog_categories'),
    # Academy
    path('panel/academy/',
         AdminAcademyView.as_view(), name='admin_academy'),
    path('panel/academy/create/',
         AdminAcademyCourseCreateView.as_view(), name='admin_academy_create'),
    path('panel/academy/<uuid:pk>/',
         AdminAcademyCourseDetailView.as_view(), name='admin_academy_course_detail'),
    path('panel/academy/<uuid:course_pk>/lessons/create/',
         AdminAcademyLessonCreateView.as_view(), name='admin_academy_lesson_create'),
    path('panel/academy/<uuid:course_pk>/lessons/<uuid:lesson_pk>/edit/',
         AdminAcademyLessonEditView.as_view(), name='admin_academy_lesson_edit'),
    path('panel/academy/enrollments/',
         AdminAcademyEnrollmentsView.as_view(), name='admin_academy_enrollments'),
    path('panel/academy/certificates/',
         AdminAcademyCertificatesView.as_view(), name='admin_academy_certificates'),
    path('panel/newsletters/',
         AdminNewslettersView.as_view(), name='admin_newsletters'),
    path('panel/contacts/',
         AdminContactsView.as_view(), name='admin_contacts'),
    path('panel/site-config/',
         AdminSiteConfigView.as_view(), name='admin_site_config'),
    path('panel/sliders/',
         AdminSlidersView.as_view(), name='admin_sliders'),
    path('panel/certificates/<uuid:cert_id>/pdf/',
         AdminCertificatePDFView.as_view(), name='admin_certificate_pdf'),
]
