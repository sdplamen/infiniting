from django.db import models
from users.models import Photographer


# Create your models here.
class Article(models.Model) :
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='articles')

    def __str__(self) :
        return self.title