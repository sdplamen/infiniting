from django.urls import path
from auctions import views

urlpatterns = [
    path('', views.AuctionListView.as_view(), name='auction-list'),
    path('create/', views.AuctionCreateView.as_view(), name='auction-create'),
    path('<int:pk>/', views.AuctionDetailView.as_view(), name='auction-detail'),
    path('<int:pk>/bid/', views.place_bid, name='auction-bid'),
]
