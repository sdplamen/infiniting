from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(User, related_name='user_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name