from django.urls import path
from photos import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='photo-home'),
    path('upload/', views.PhotoCreateView.as_view(), name='photo-create'),
    path('<int:pk>/', views.PhotoDetailView.as_view(), name='photo-detail'),
    path('<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='photo-edit'),
    path('<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='photo-delete'),
    path('<int:pk>/like/', views.like_photo, name='photo-like'),
    path('<int:pk>/unlike/', views.unlike_photo, name='photo-unlike'),
    path('<int:pk>/comment/', views.PhotoAddCommentView.as_view(), name='photo-comment'),
    path('<int:pk>/rate/', views.PhotoAddRatingView.as_view(), name='photo-rate'),
]