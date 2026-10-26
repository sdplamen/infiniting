from django.urls import path
from users import views

urlpatterns = [
    path('', views.ProfileListView.as_view(), name='user-profile-list'),
    path('create/', views.ProfileCreateView.as_view(), name='user-profile-create'),
    path('<int:pk>/', views.ProfileDetailView.as_view(), name='user-profile-detail'),
    path('<int:pk>/edit/', views.ProfileUpdateView.as_view(), name='user-profile-edit'),
    path('<int:pk>/delete/', views.ProfileDeleteView.as_view(), name='user-profile-delete'),
    path('<int:pk>/follow/', views.follow_user, name='user-follow'),
    path('<int:pk>/unfollow/', views.unfollow_user, name='user-unfollow'),
    path('me/', views.ProfileDetailView.as_view(), name='user-profile'),
]
