from django import template
from users.models import Follow

register = template.Library()

@register.filter
def is_following(user, other_user):
    return Follow.objects.filter(follower=user, followed=other_user).exists()
