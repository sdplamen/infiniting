from django.db import models, transaction
from django.db.models import Max, Q

from photos.models import Photo
from users.models import Photographer


class Essay(models.Model):
    """A photographer's sequenced set of their own photos: a photo essay told
    in order with editorial captions, or a contact sheet of numbered frames."""

    class Kind(models.TextChoices):
        ESSAY = 'essay', 'Фотоесе'
        CONTACT_SHEET = 'contact_sheet', 'Контактен лист'

    class CoverLayout(models.TextChoices):
        FULL_BLEED = 'full_bleed', 'Цял кадър: снимката на цял екран, заглавието върху нея'
        SPLIT = 'split', 'Разделен: снимката вляво, заглавието и увода вдясно'
        TRIPTYCH = 'triptych', 'Триптих: първите три кадъра един до друг'
        TYPOGRAPHIC = 'typographic', 'Типографски: само заглавие и увод, без снимка'

    author = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='essays')
    title = models.CharField('Заглавие', max_length=120)
    intro = models.TextField('Увод', blank=True)
    kind = models.CharField('Вид', max_length=20, choices=Kind.choices, default=Kind.ESSAY)
    cover_layout = models.CharField('Корица', max_length=20, choices=CoverLayout.choices,
                                    default=CoverLayout.FULL_BLEED)
    cover_photo = models.ForeignKey(Photo, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='+', verbose_name='Снимка за корицата')
    is_published = models.BooleanField('Публикувано', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    @classmethod
    def visible_to(cls, user):
        """Published essays, plus the user's own drafts."""
        visible = Q(is_published=True)
        if user.is_authenticated:
            visible |= Q(author__user=user)
        return cls.objects.filter(visible)

    def is_owned_by(self, user):
        return user.is_authenticated and self.author.user_id == user.id

    @property
    def cover(self):
        """The chosen cover photo, or the first frame of the sequence."""
        if self.cover_photo_id:
            return self.cover_photo
        first = self.items.select_related('photo').first()
        return first.photo if first else None

    def triptych(self):
        """Up to three photos for the triptych cover: the chosen cover photo first,
        then the sequence's first frames."""
        photos = [item.photo for item in self.items.select_related('photo')[:3]]
        if self.cover_photo_id:
            photos = [self.cover_photo] + [p for p in photos if p.pk != self.cover_photo_id][:2]
        return photos

    def append_photos(self, photos):
        """Add photos to the end of the sequence, skipping ones already in it."""
        with transaction.atomic():
            present = set(self.items.values_list('photo_id', flat=True))
            position = self.items.aggregate(m=Max('position'))['m'] or 0
            new_items = []
            for photo in photos:
                if photo.pk in present:
                    continue
                position += 1
                present.add(photo.pk)
                new_items.append(EssayItem(essay=self, photo=photo, position=position))
            EssayItem.objects.bulk_create(new_items)
        return new_items

    def reorder(self, item_ids):
        """Set the sequence to `item_ids` (this essay's item ids, in the new order).
        Raises ValueError unless it lists each of the essay's items exactly once."""
        items = {item.pk: item for item in self.items.all()}
        if sorted(item_ids) != sorted(items) or len(set(item_ids)) != len(item_ids):
            raise ValueError('The new order must list every item of the essay once.')
        for position, item_id in enumerate(item_ids, start=1):
            items[item_id].position = position
        EssayItem.objects.bulk_update(items.values(), ['position'])


class EssayItem(models.Model):
    """One frame of an essay: a photo at a position, with an editorial caption
    that belongs to the essay (the photo keeps its own caption elsewhere)."""
    essay = models.ForeignKey(Essay, on_delete=models.CASCADE, related_name='items')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='essay_items')
    position = models.PositiveIntegerField()
    caption = models.TextField('Текст към кадъра', blank=True)

    class Meta:
        ordering = ['position', 'pk']
        constraints = [
            models.UniqueConstraint(fields=['essay', 'photo'], name='essay_photo_once'),
        ]

    def __str__(self):
        return f'{self.essay} #{self.position}'
