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


class ProfileDetailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.photographer = kwargs.pop('photographer', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def can_edit_delete_profile(self):
        return self.user.is_authenticated and self.user == self.photographer.user

    def can_leave_group(self, group):
        return self.user.is_authenticated and self.user in group.members.all()
