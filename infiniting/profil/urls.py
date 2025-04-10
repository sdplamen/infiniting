from django.urls import path
from profil import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
]
