from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='user_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        permissions = [('can_approve_groups', 'Can approve new groups')]

    def __str__(self):
        return self.name