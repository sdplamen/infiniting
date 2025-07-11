from django import forms
from .models import Group


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description']

class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'members']


class GroupDetailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def is_member(self):
        if not self.user or not self.user.is_authenticated:
            return False
        return self.user in self.group.members.all()

    def can_edit_group(self):
        return self.is_member()