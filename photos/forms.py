import base64
import binascii
import io

from django import forms
from groups.models import Group
from .direct_upload import verified_resource
from .exif import extract_exif
from .models import Photo, Comment, Rating

EXIF_HEAD_BYTES = 64 * 1024   # a JPEG's EXIF block (APP1) is at most 64 KB and sits at the start


class PhotoUploadForm(forms.ModelForm):
    """Takes the photo either as a normal file upload, or (static/js/direct-upload.js) as the
    reference to a file the browser already uploaded to Cloudinary plus the file's first
    64 KB, from which the EXIF is read here exactly as for a normal upload."""

    direct_public_id = forms.CharField(required=False, widget=forms.HiddenInput)
    direct_version = forms.CharField(required=False, widget=forms.HiddenInput)
    direct_format = forms.CharField(required=False, widget=forms.HiddenInput)
    direct_signature = forms.CharField(required=False, widget=forms.HiddenInput)
    exif_head = forms.CharField(required=False, widget=forms.HiddenInput,
                                max_length=EXIF_HEAD_BYTES * 4 // 3 + 4)   # base64

    class Meta:
        model = Photo
        fields = ['image', 'caption', 'group']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False      # checked in clean(): a file or a direct upload
        self.fields['image'].widget.attrs.update({'accept': 'image/*', 'data-direct-upload': 'photo'})
        if user is not None:
            # approved groups, plus unapproved ones the user created or belongs to
            self.fields['group'].queryset = Group.visible_to(user).order_by('name')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('direct_public_id'):
            resource = verified_resource(cleaned['direct_public_id'], cleaned.get('direct_version'),
                                         cleaned.get('direct_signature'), cleaned.get('direct_format'))
            if resource is None:
                raise forms.ValidationError('Качването не можа да бъде потвърдено. Изберете снимката отново.')
            cleaned['image'] = resource
            self.instance.exif = self._exif_from_head(cleaned.get('exif_head'))
        elif not cleaned.get('image'):
            self.add_error('image', 'Изберете снимка.')
        return cleaned

    @staticmethod
    def _exif_from_head(encoded):
        try:
            head = base64.b64decode(encoded or '', validate=True)[:EXIF_HEAD_BYTES]
        except (binascii.Error, ValueError):
            return {}
        return extract_exif(io.BytesIO(head)) if head else {}

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Коментар'}
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }


class PhotoDetailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.photo = kwargs.pop('photo', None)
        self.user = kwargs.pop('user', None)
        self.user_liked = kwargs.pop('user_liked', False)
        self.user_rating = kwargs.pop('user_rating', None)
        super().__init__(*args, **kwargs)

    def can_like_or_rate(self):
        return self.user and self.user.is_authenticated

    def has_liked(self):
        return self.user_liked

    def has_rated(self):
        return self.user_rating is not None

    def can_edit_delete(self):
        return self.user and self.user.is_authenticated and self.user == self.photo.author.user
