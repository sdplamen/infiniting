"""`{{ photo.image|img:'card' }}`: a Cloudinary delivery URL resized for where the image is shown,
in the best format the browser accepts (f_auto: AVIF or WebP, else JPEG) and automatic quality.
Cloudinary makes each variant on first request and caches it, so nothing is processed in our
requests. Registered as a template builtin in settings.TEMPLATES, so no {% load %} is needed."""
from cloudinary import CloudinaryResource
from django import template

register = template.Library()

_AUTO = {'fetch_format': 'auto', 'quality': 'auto', 'secure': True}

VARIANTS = {
    'thumb': {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'auto'},    # pickers, editor rows
    'avatar': {'width': 320, 'height': 320, 'crop': 'fill', 'gravity': 'face'},   # profile pictures
    'card': {'width': 900, 'crop': 'limit'},                                       # feed and list cards
    'large': {'width': 1600, 'crop': 'limit'},                                     # photo page, essay frames
    'full': {'quality': 'auto:best'},                                              # lightbox loupe: every pixel
}


@register.filter
def img(image, variant='card'):
    if not image:
        return ''
    if isinstance(image, CloudinaryResource):
        return image.build_url(**{**_AUTO, **VARIANTS[variant]})
    return getattr(image, 'url', image)   # a plain file or URL: as it is
