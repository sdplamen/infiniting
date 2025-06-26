from django.urls import path
from profil import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('profiles/', views.PhotographerProfileListView.as_view(), name='profile-list'),
    path('profiles/create/', views.PhotographerProfileCreateView.as_view(), name='profile-create'),
    path('profiles/<int:profil_pk>/details/', views.PhotographerProfileDetailView.as_view(), name='profile-details'),
    path('profiles/<int:profil_pk>/edit/', views.PhotographerProfileUpdateView.as_view(), name='profile-edit'),
    path('profiles/<int:profil_pk>/delete/', views.PhotographerProfileDeleteView.as_view(), name='profile-delete'),
    path('profile/', views.PhotographerProfileDetailView.as_view(), name='my-profile-details'),

    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group-create'),
    path('groups/<int:group_pk>/details/', views.GroupDetailView.as_view(), name='group-details'),
    path('groups/<int:group_pk>/edit/', views.GroupUpdateView.as_view(), name='group-edit'),
    path('groups/<int:group_pk>/delete/', views.GroupDeleteView.as_view(), name='group-delete'),
    path('groups/<int:group_pk>/join/', views.join_group, name='join-group'),
    path('groups/<int:group_pk>/leave/', views.leave_group, name='leave-group'),

    path('photos/upload/', views.PhotoCreateView.as_view(), name='photo-upload'),
    path('photos/<int:photo_pk>/details/', views.PhotoDetailView.as_view(), name='photo-details'),
    path('photos/<int:photo_pk>/edit/', views.PhotoUpdateView.as_view(), name='photo-edit'),
    path('photos/<int:photo_pk>/delete/', views.PhotoDeleteView.as_view(), name='photo-delete'),
    path('photos/<int:photo_pk>/like/', views.like_photo, name='like-photo'),
    path('photos/<int:photo_pk>/unlike/', views.unlike_photo, name='unlike-photo'),
    path('photos/<int:photo_pk>/comment/', views.add_comment, name='add-comment'),
    path('photos/<int:photo_pk>/rate/', views.add_rating, name='add-rating'),

    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article-create'),
    path('articles/<int:article_pk>/details/', views.ArticleDetailView.as_view(), name='article-details'),
    path('articles/<int:article_pk>/edit/', views.ArticleUpdateView.as_view(), name='article-edit'),
    path('articles/<int:article_pk>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),

    path('auctions/', views.AuctionListView.as_view(), name='auction-list'),
    path('auctions/create/', views.AuctionCreateView.as_view(), name='auction-create'),  # For admin/staff to create
    path('auctions/<int:auction_pk>/details/', views.AuctionDetailView.as_view(), name='auction-details'),
    path('auctions/<int:auction_pk>/bid/', views.place_bid, name='place-bid'),
]
