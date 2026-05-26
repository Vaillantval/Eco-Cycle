from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.WasteCategoryListView.as_view(), name='waste_categories'),
    path('listings/', views.WasteListingListCreateView.as_view(), name='waste_listings'),
    path('listings/<uuid:pk>/', views.WasteListingDetailView.as_view(), name='waste_listing_detail'),
    path('analyze/', views.AIAnalysisView.as_view(), name='waste_analyze'),
    path('advisor/', views.RecyclingAdvisorView.as_view(), name='recycling_advisor'),
    path('admin/listings/', views.AdminListingListView.as_view()),
    path('admin/listings/<uuid:pk>/review/', views.AdminReviewListingView.as_view()),
]
