from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from django.urls import path
from mobileAPI.views import RegisterView, PhotoListCreateAPIView, PhotoDetailAPIView, LikeListCreateAPIView, LikeDetailAPIView, CommentListCreateAPIView, CommentDetailAPIView, RatingListCreateAPIView, RatingDetailAPIView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('register/', RegisterView.as_view(), name='register'),  # Removed duplicate
    path('photos/', PhotoListCreateAPIView.as_view(), name='photo-list-create'),
    path('photos/<int:pk>/', PhotoDetailAPIView.as_view(), name='photo-detail-api'),
    path('likes/', LikeListCreateAPIView.as_view(), name='like-list-create'),
    path('likes/<int:pk>/', LikeDetailAPIView.as_view(), name='like-detail'),
    path('comments/', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailAPIView.as_view(), name='comment-detail'),
    path('ratings/', RatingListCreateAPIView.as_view(), name='rating-list-create'),
    path('ratings/<int:pk>/', RatingDetailAPIView.as_view(), name='rating-detail'),
]
