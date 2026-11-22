from django import forms
from .models import Group, GroupComment


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description']

class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'members']


class GroupCommentForm(forms.ModelForm):
    class Meta:
        model = GroupComment
        fields = ['text']
        labels = {'text': 'Коментар'}
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}


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
        """Author or staff: same rule as the edit/delete views."""
        if not self.user or not self.user.is_authenticated:
            return False
        return self.user.is_staff or self.group.author_id == self.user.id

    def can_user_approve(self):
        if not self.user or not self.user.is_authenticated:
            return False
        return not self.group.is_approved and (self.user.is_staff or self.user.is_superuser)