from django.urls import path
from groups import views

urlpatterns = [
    path('', views.GroupListView.as_view(), name='group-list'),
    path('create/', views.GroupCreateView.as_view(), name='group-create'),
    path('<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group-edit'),
    path('<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group-delete'),
    path('<int:pk>/join/', views.join_group, name='group-join'),
    path('<int:pk>/leave/', views.leave_group, name='group-leave'),
]
