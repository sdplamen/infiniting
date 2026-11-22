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

    @classmethod
    def visible_to(cls, user):
        """Approved groups, plus unapproved ones for staff, their author and existing members."""
        queryset = cls.objects.all()
        if user.is_authenticated and user.is_staff:
            return queryset
        visible = models.Q(is_approved=True)
        if user.is_authenticated:
            visible |= models.Q(author=user) | models.Q(members=user)
        return queryset.filter(visible).distinct()


class GroupComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_comments')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user.username} in group {self.group_id}'
