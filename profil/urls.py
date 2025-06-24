from django.urls import path
from profil import views

urlpatterns = [
    path('', views.homepage_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('groups/', views.group_list_view, name='group'),
    path('articles/', views.article_list_view, name='article'),
    path('auctions/', views.auction_list_view, name='auction'),
    path('author/<int:author_id>/', views.author_detail_view, name='author_detail')
]
