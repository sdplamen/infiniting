from django.shortcuts import render
from .models import Author, Group, Photo

# Create your views here.
def homepage_view(request):
    return render(request, 'profil.html')

def profile_view(request):
    return render(request, 'profil.html')

def group_list_view(request):
    return render(request, 'group.html')

def article_list_view(request):
    return render(request, 'article.html')

def auction_list_view(request):
    return render(request, 'auction.html')

def author_detail_view(request, author_id):
    return render(request, 'author_detail.html')