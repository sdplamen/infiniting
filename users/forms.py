from django import forms
from .models import Photographer
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