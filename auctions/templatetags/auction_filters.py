from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def is_future(value):
    if not value:
        return False
    return value > timezone.now()