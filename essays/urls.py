from django.urls import path

from essays import views

urlpatterns = [
    path('', views.EssayListView.as_view(), name='essay-list'),
    path('create/', views.EssayCreateView.as_view(), name='essay-create'),
    path('<int:pk>/', views.EssayDetailView.as_view(), name='essay-detail'),
    path('<int:pk>/edit/', views.EssayUpdateView.as_view(), name='essay-edit'),
    path('<int:pk>/sequence/', views.EssaySequenceView.as_view(), name='essay-sequence'),
    path('<int:pk>/sequence/add/', views.EssayAddPhotosView.as_view(), name='essay-add-photos'),
    path('<int:pk>/delete/', views.EssayDeleteView.as_view(), name='essay-delete'),
]
