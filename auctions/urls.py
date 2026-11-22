from django.urls import path
from auctions import views

urlpatterns = [
    path('', views.AuctionListView.as_view(), name='auction-list'),
    path('create/', views.AuctionCreateView.as_view(), name='auction-create'),
    path('<int:pk>/', views.AuctionDetailView.as_view(), name='auction-detail'),
    path('<int:pk>/bid/', views.place_bid, name='auction-bid'),
    path('<int:pk>/deactivate/', views.AuctionDeactivateView.as_view(), name='auction-deactivate'),
    path('<int:pk>/payment/', views.PaymentView.as_view(), name='auction-payment'),
    path('<int:pk>/comment/', views.add_auction_comment, name='auction-comment'),
    path('<int:pk>/comment/<int:comment_pk>/delete/', views.delete_auction_comment, name='auction-comment-delete'),
]
