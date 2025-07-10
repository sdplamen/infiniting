from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from groups.models import Group
from users.models import Photographer


# Create your models here.
class Photo(models.Model):
    author = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='photos')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    image = models.ImageField(upload_to='photographer_pictures/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo by {self.author.user.username} - {self.caption if self.caption else self.id}'

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photo') # A user can only like a photo once

    def __str__(self):
        return f'{self.user.username} likes {self.photo.id}'

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.photo.id}'

class Rating(models.Model):
    user = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='ratings')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photo')

    def __str__(self):
        return f'{self.user.username} rated {self.photo.id} with {self.score}'