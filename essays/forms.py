from django import forms

from essays.models import Essay
from photos.models import Photo


class PhotoChoiceField(forms.ModelMultipleChoiceField):
    """Photos as checkboxes; the template renders them as thumbnails."""
    widget = forms.CheckboxSelectMultiple

    def label_from_instance(self, photo):
        return photo.caption or 'Без заглавие'


class EssayForm(forms.ModelForm):
    """Title, intro, kind, cover and publishing. On create it also takes the
    first photos; the cover can only be one of the essay's own photos."""

    photos = PhotoChoiceField(queryset=Photo.objects.none(), required=False, label='Снимки',
                              help_text='По-късно можете да добавяте още и да ги подреждате.')

    class Meta:
        model = Essay
        fields = ['title', 'intro', 'kind', 'cover_layout', 'cover_photo', 'is_published']
        widgets = {
            'intro': forms.Textarea(attrs={'rows': 4}),
            'kind': forms.RadioSelect,
            'cover_layout': forms.RadioSelect,
        }
        help_texts = {
            'kind': 'Есето се чете кадър по кадър с текст; контактният лист показва всички кадри в мрежа.',
            'cover_photo': 'Ако не изберете, корицата е първият кадър.',
            'is_published': 'Чернова виждате само вие.',
        }

    def __init__(self, *args, photographer, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['photos']
            self.fields['cover_photo'].queryset = Photo.objects.filter(essay_items__essay=self.instance)
            self.fields['cover_photo'].empty_label = 'Първият кадър'
        else:
            del self.fields['cover_photo']  # no photos to choose from yet
            self.fields['photos'].queryset = photographer.photos.order_by('uploaded_at')


class AddPhotosForm(forms.Form):
    photos = PhotoChoiceField(queryset=Photo.objects.none(), label='Добави снимки')

    def __init__(self, *args, essay, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photos'].queryset = (essay.author.photos.exclude(essay_items__essay=essay)
                                          .order_by('-uploaded_at'))
