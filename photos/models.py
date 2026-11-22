from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from groups.models import Group
from photos.exif import EXIF_LABELS, extract_exif
from users.models import Photographer

User = get_user_model()
# Create your models here.
class Photo(models.Model):
    author = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='photos')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    image = CloudinaryField(folder='photos',)
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # camera/exposure details read from the file at upload (see photos/exif.py)
    exif = models.JSONField(default=dict, blank=True, editable=False)

    def __str__(self):
        return f'Photo by {self.author} - {self.caption or self.id}'

    def save(self, *args, **kwargs):
        # A new file is still an UploadedFile here; CloudinaryField swaps it for
        # the Cloudinary resource during super().save(), so read EXIF first.
        # Covers the web form, the mobile API and the admin.
        if isinstance(self.image, UploadedFile):
            self.exif = extract_exif(self.image)
        super().save(*args, **kwargs)

    @property
    def exif_items(self):
        """[(label, value), ...] in display order, for the template."""
        return [(label, self.exif[key]) for key, label in EXIF_LABELS.items() if self.exif.get(key)]

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
        return f'{self.user} rated {self.photo.id} with {self.score}'