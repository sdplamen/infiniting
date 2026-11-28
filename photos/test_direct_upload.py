"""Direct browser → Cloudinary uploads (photos/direct_upload.py) and delivery variants (|img)."""
import base64
import io
from unittest import mock

import cloudinary
from cloudinary import CloudinaryResource
from cloudinary.utils import api_sign_request
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from photos.exif import extract_exif
from photos.models import Photo
from photos.tests import jpeg_with_exif

UserModel = get_user_model()
SECRET = 'test-secret'
FAKE_UPLOAD = CloudinaryResource('photos/server', format='jpg', version=1, type='upload',
                                 resource_type='image', metadata={})


def big_jpeg_with_exif():
    """A JPEG well over 64 KB, with EXIF, so only its head is sent for EXIF."""
    image = Image.effect_noise((1600, 1200), 80).convert('RGB')
    small = Image.open(io.BytesIO(jpeg_with_exif()))
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=95, exif=small.getexif())
    return buffer.getvalue()


class DirectUploadTestCase(TestCase):
    def setUp(self):
        config = cloudinary.config()
        saved = (config.cloud_name, config.api_key, config.api_secret)
        cloudinary.config(cloud_name='demo', api_key='1234', api_secret=SECRET)
        self.addCleanup(lambda: cloudinary.config(cloud_name=saved[0], api_key=saved[1], api_secret=saved[2]))
        self.user = UserModel.objects.create_user(username='uploader', password='pw-12345678')
        self.client.force_login(self.user)

    def reference(self, public_id='photos/abc123', version='1712345678', fmt='jpg', head=b''):
        """The fields direct-upload.js posts after Cloudinary accepted the file."""
        return {
            'direct_public_id': public_id,
            'direct_version': version,
            'direct_format': fmt,
            'direct_signature': api_sign_request({'public_id': public_id, 'version': version}, SECRET),
            'exif_head': base64.b64encode(head).decode(),
        }


class SignUploadTest(DirectUploadTestCase):
    def test_signs_a_photos_folder_upload(self):
        response = self.client.post(reverse('photo-upload-sign'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual((data['folder'], data['api_key']), ('photos', '1234'))
        self.assertEqual(data['upload_url'], 'https://api.cloudinary.com/v1_1/demo/image/upload')
        signed = {key: data[key] for key in ('timestamp', 'folder', 'allowed_formats')}
        self.assertEqual(data['signature'], api_sign_request(signed, SECRET))
        self.assertNotIn(SECRET, response.content.decode())

    def test_only_signed_in_posts(self):
        self.assertEqual(self.client.get(reverse('photo-upload-sign')).status_code, 405)
        self.client.logout()
        response = self.client.post(reverse('photo-upload-sign'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('photo-upload-sign')}")

    def test_upload_page_wires_the_script(self):
        page = self.client.get(reverse('photo-create'))
        self.assertContains(page, f'data-sign-url="{reverse("photo-upload-sign")}"')
        self.assertContains(page, 'data-direct-upload="photo"')
        self.assertContains(page, 'js/direct-upload.js')
        self.assertContains(page, 'type="hidden" name="direct_public_id"')
        self.assertNotContains(page, '<label for="id_direct_public_id"')   # hidden fields get no labels


@mock.patch('cloudinary.models.uploader.upload_resource', return_value=FAKE_UPLOAD)
class CreateFromDirectUploadTest(DirectUploadTestCase):
    def test_publishing_saves_the_reference_without_uploading_again(self, upload):
        head = big_jpeg_with_exif()[:64 * 1024]
        response = self.client.post(reverse('photo-create'), {'caption': 'Мост', **self.reference(head=head)})
        self.assertRedirects(response, reverse('photo-home'))
        upload.assert_not_called()                          # the browser already uploaded it
        photo = Photo.objects.get()
        self.assertEqual((photo.image.public_id, photo.image.version, photo.image.format),
                         ('photos/abc123', '1712345678', 'jpg'))
        self.assertEqual(photo.author, self.user.photographer)
        self.assertEqual(photo.exif['camera'], 'Canon EOS R6')   # read from the first 64 KB only
        self.assertNotIn('gps', str(photo.exif).lower())

    def test_forged_or_foreign_references_are_refused(self, upload):
        cases = {
            'forged signature': {**self.reference(), 'direct_signature': 'f' * 40},
            'other folder': self.reference(public_id='avatars/someone'),
            'bad version': self.reference(version='12a'),
            'bad format': self.reference(fmt='j/pg'),
        }
        for name, data in cases.items():
            with self.subTest(name):
                response = self.client.post(reverse('photo-create'), {'caption': 'x', **data})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Качването не можа да бъде потвърдено.')
        self.assertFalse(Photo.objects.exists())

    def test_no_file_and_no_reference(self, upload):
        response = self.client.post(reverse('photo-create'), {'caption': 'x'})
        self.assertContains(response, 'Изберете снимка.')
        self.assertFalse(Photo.objects.exists())

    def test_without_javascript_the_file_uploads_as_before(self, upload):
        file = SimpleUploadedFile('p.jpg', jpeg_with_exif(), content_type='image/jpeg')
        response = self.client.post(reverse('photo-create'), {'caption': 'обикновено', 'image': file})
        self.assertRedirects(response, reverse('photo-home'))
        upload.assert_called_once()
        self.assertEqual(Photo.objects.get().exif['camera'], 'Canon EOS R6')

    def test_bad_exif_head_still_publishes(self, upload):
        data = {**self.reference(), 'exif_head': 'not base64!'}
        self.assertRedirects(self.client.post(reverse('photo-create'), {'caption': 'x', **data}), reverse('photo-home'))
        self.assertEqual(Photo.objects.get().exif, {})


@mock.patch('cloudinary.models.uploader.upload_resource', return_value=FAKE_UPLOAD)
class EditWithDirectUploadTest(DirectUploadTestCase):
    def setUp(self):
        super().setUp()
        self.photo = Photo.objects.create(author=self.user.photographer, image='photos/old', caption='стара',
                                          exif={'camera': 'Leica M6'})
        self.url = reverse('photo-edit', kwargs={'pk': self.photo.pk})

    def test_replacing_the_image(self, upload):
        response = self.client.post(self.url, {'caption': 'нова', **self.reference(public_id='photos/new')})
        self.assertRedirects(response, reverse('photo-detail', kwargs={'pk': self.photo.pk}))
        self.photo.refresh_from_db()
        self.assertEqual((self.photo.image.public_id, self.photo.caption), ('photos/new', 'нова'))
        self.assertEqual(self.photo.exif, {})               # new image without EXIF: old data cleared
        upload.assert_not_called()

    def test_editing_only_the_caption_keeps_the_image(self, upload):
        response = self.client.post(self.url, {'caption': 'само текст'})
        self.assertRedirects(response, reverse('photo-detail', kwargs={'pk': self.photo.pk}))
        self.photo.refresh_from_db()
        self.assertEqual((self.photo.image.public_id, self.photo.exif), ('photos/old', {'camera': 'Leica M6'}))


class ExifHeadTest(TestCase):
    def test_first_64_kb_of_a_large_jpeg_is_enough(self):
        data = big_jpeg_with_exif()
        self.assertGreater(len(data), 256 * 1024)
        self.assertEqual(extract_exif(io.BytesIO(data[:64 * 1024])), extract_exif(io.BytesIO(data)))


class ImageVariantTest(TestCase):
    def render(self, variant, image):
        return Template("{{ image|img:'" + variant + "' }}").render(Context({'image': image}))

    def test_variants_are_resized_and_auto_format(self):
        image = CloudinaryResource('photos/abc', format='jpg', version='17', type='upload', resource_type='image')
        card = self.render('card', image)
        self.assertIn('/image/upload/', card)
        self.assertIn('f_auto', card)
        self.assertIn('q_auto', card)
        self.assertIn('w_900', card)
        self.assertIn('c_limit', card)
        self.assertIn('w_400', self.render('thumb', image))
        self.assertIn('g_face', self.render('avatar', image))
        full = self.render('full', image)
        self.assertIn('q_auto:best', full)
        self.assertNotIn('w_', full)                         # the loupe gets every pixel
        self.assertTrue(card.startswith('https://'))

    def test_empty_and_plain_values(self):
        self.assertEqual(self.render('card', None), '')
        self.assertEqual(self.render('card', '/static/x.jpg'), '/static/x.jpg')
