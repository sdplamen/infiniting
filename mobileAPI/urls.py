from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from django.urls import path
from mobileAPI.views import RegisterView, PhotoListCreateAPIView, PhotoDetailAPIView, LikeListCreateAPIView, \
    LikeDetailAPIView, CommentListCreateAPIView, CommentDetailAPIView, RatingListCreateAPIView, RatingDetailAPIView, \
    ArticleListCreateAPIView, ArticleDetailAPIView, AuctionListCreateAPIView, AuctionDetailAPIView, \
    BidListCreateAPIView, BidDetailAPIView, GroupListCreateAPIView, GroupDetailAPIView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register-api'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('photos/', PhotoListCreateAPIView.as_view(), name='photo-list-create'),
    path('photos/<int:pk>/', PhotoDetailAPIView.as_view(), name='photo-detail-api'),
    path('likes/', LikeListCreateAPIView.as_view(), name='like-list-create'),
    path('likes/<int:pk>/', LikeDetailAPIView.as_view(), name='like-detail'),
    path('comments/', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailAPIView.as_view(), name='comment-detail'),
    path('ratings/', RatingListCreateAPIView.as_view(), name='rating-list-create'),
    path('ratings/<int:pk>/', RatingDetailAPIView.as_view(), name='rating-detail'),
    path('articles/', ArticleListCreateAPIView.as_view(), name='article-list-create'),
    path('articles/<int:pk>/', ArticleDetailAPIView.as_view(), name='article-detail-api'),
    path('auctions/', AuctionListCreateAPIView.as_view(), name='auction-list-create'),
    path('auctions/<int:pk>/', AuctionDetailAPIView.as_view(), name='auction-detail-api'),
    path('bids/', BidListCreateAPIView.as_view(), name='bid-list-create'),
    path('bids/<int:pk>/', BidDetailAPIView.as_view(), name='bid-detail'),
    path('groups/', GroupListCreateAPIView.as_view(), name='group-list-create'),
    path('groups/<int:pk>/', GroupDetailAPIView.as_view(), name='group-detail-api'),

]
