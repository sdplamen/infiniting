from django.urls import path
from photos import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='photo-home'),
    path('upload/', views.PhotoCreateView.as_view(), name='photo-create'),
    path('upload/sign/', views.sign_upload, name='photo-upload-sign'),
    path('<int:pk>/photo-detail/', views.PhotoDetailView.as_view(), name='photo-detail'),
    path('<int:pk>/full-photo/', views.FullPhotoView.as_view(), name='photo-full-photo'),
    path('<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='photo-edit'),
    path('<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='photo-delete'),
    path('<int:pk>/like/', views.like_photo, name='photo-like'),
    path('<int:pk>/unlike/', views.unlike_photo, name='photo-unlike'),
    path('<int:pk>/bookmark/', views.bookmark_photo, name='photo-bookmark'),
    path('<int:pk>/unbookmark/', views.unbookmark_photo, name='photo-unbookmark'),
    path('saved/', views.SavedPhotosView.as_view(), name='photo-saved'),
    path('<int:pk>/comment/', views.PhotoAddCommentView.as_view(), name='photo-comment'),
    path('<int:pk>/comment/<int:comment_pk>/delete/', views.delete_comment, name='photo-comment-delete'),
    path('<int:pk>/rate/', views.PhotoAddRatingView.as_view(), name='photo-rate'),
]