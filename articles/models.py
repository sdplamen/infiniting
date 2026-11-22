from django.contrib.auth import get_user_model
from django.db import models
from users.models import Photographer

User = get_user_model()
# Create your models here.
class Article(models.Model) :
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='articles')
    is_approved = models.BooleanField(default=False)

    class Meta :
        permissions = [('can_approve_articles', 'Can approve articles'),]

    def __str__(self) :
        return self.title


class ArticleComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_comments')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on article {self.article_id}'
