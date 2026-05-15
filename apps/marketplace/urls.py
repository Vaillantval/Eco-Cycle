from django.urls import path
from . import views

urlpatterns = [
    path('auctions/', views.PublicAuctionListView.as_view(), name='auction_list'),
    path('auctions/create/', views.CreateAuctionView.as_view(), name='auction_create'),
    path('auctions/<uuid:pk>/', views.AuctionDetailView.as_view(), name='auction_detail'),
    path('auctions/<uuid:pk>/bid/', views.PlaceBidView.as_view(), name='auction_bid'),
    path('auctions/<uuid:pk>/buy-now/', views.BuyNowView.as_view(), name='auction_buy_now'),
    path('orders/my/', views.MyOrdersView.as_view(), name='my_orders'),
    path('orders/sales/', views.MySalesView.as_view(), name='my_sales'),
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin_orders'),
]
