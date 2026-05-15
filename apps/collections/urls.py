from django.urls import path
from . import views

urlpatterns = [
    path('', views.PickupRequestListCreateView.as_view(), name='pickup_list_create'),
    path('admin/', views.AdminPickupListView.as_view(), name='admin_pickup_list'),
    path('collector/', views.CollectorPickupListView.as_view(), name='collector_pickups'),
    path('<uuid:pk>/', views.PickupRequestDetailView.as_view()),
    path('<uuid:pk>/assign/', views.AssignCollectorView.as_view(), name='pickup_assign'),
    path('<uuid:pk>/status/', views.UpdatePickupStatusView.as_view(), name='pickup_status'),
]
