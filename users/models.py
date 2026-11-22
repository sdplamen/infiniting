from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()
# Create your models here.
class Photographer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='photographer')
    bio = models.TextField(blank=True, null=True)
    profile_picture = CloudinaryField(folder='profiles', blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Follow(models.Model) :
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta :
        unique_together = ('follower', 'followed')

    def __str__(self) :
        return f'{self.follower.username} follows {self.followed.username}'


class ProfileComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_comments')
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on profile {self.photographer_id}'
