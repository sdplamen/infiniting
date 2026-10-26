from django import forms
from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content']


class ArticleDetailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def can_user_edit_delete(self):
        if not self.user or not self.user.is_authenticated:
            return False
        return self.article.author.user == self.user

    def can_user_approve(self):
        if not self.user or not self.user.is_authenticated:
            return False
        return not self.article.is_approved and self.user.has_perm('articles.can_approve_articles')
