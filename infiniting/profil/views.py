from django.shortcuts import render
from .models import Author, Group, Photo

# Create your views here.
def homepage_view(request):
    return render(request, 'profil/homepage.html')

def profile_view(request):
    return render(request, 'profil/profil.html')

def group_list_view(request):
    return render(request, 'profil/group_list.html')

def article_list_view(request):
    return render(request, 'profil/article_list.html')

def auction_list_view(request):
    return render(request, 'profil/auction_list.html')

def author_detail_view(request, author_id):
    return render(request, 'profil/author_detail.html')