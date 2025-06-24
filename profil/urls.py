from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage_view, name='homepage'),
    path('profile/', views.profile_view, name='profile_view_name'),
    path('groups/', views.group_list_view, name='group_view_name'),
    path('articles/', views.article_list_view, name='article_view_name'),
    path('auctions/', views.auction_list_view, name='auction_view_name'),
    path('author/<int:author_id>/', views.author_detail_view, name='author_detail')
]
