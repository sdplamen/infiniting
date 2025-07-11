from django import forms
from .models import Photo, Comment, Rating


class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'caption', 'group']

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


class PhotoDetailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.photo = kwargs.pop('photo', None)
        self.user = kwargs.pop('user', None)
        self.user_liked = kwargs.pop('user_liked', False)
        self.user_rating = kwargs.pop('user_rating', None)
        super().__init__(*args, **kwargs)

    def can_like_or_rate(self):
        return self.user and self.user.is_authenticated

    def has_liked(self):
        return self.user_liked

    def has_rated(self):
        return self.user_rating is not None

    def can_edit_delete(self):
        return self.user and self.user.is_authenticated and self.user == self.photo.author.user
