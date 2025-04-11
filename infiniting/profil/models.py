from django.db import models

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='authors/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(Author, related_name='groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Photo(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='photos')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    image = models.ImageField(upload_to='photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo by {self.author.name} - {self.caption if self.caption else self.id}'