from django import forms
from .models import Photographer, Group, Photo, Article, Like, Comment, Rating, Auction, Bid
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class PhotographerProfileForm(forms.ModelForm):
    class Meta:
        model = Photographer
        fields = ['name', 'bio', 'profile_picture']

class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description']

class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'members']

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'caption', 'group']

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

class AuctionCreateForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['photo', 'start_time', 'end_time', 'starting_bid']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']