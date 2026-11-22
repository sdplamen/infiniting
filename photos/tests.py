import os, io
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from photos.models import Photo, Photographer, Group
from django.conf import settings

UserModel = get_user_model()

class PhotoUploadIntegrationTest(TestCase) :
    def setUp(self) :
        self.client = Client()
        self.user = UserModel.objects.create_user(
            username='testuser',
            password='testpassword123'
        )
        self.client.login(username='testuser', password='testpassword123')
        self.group = Group.objects.create(name='Test Group')

    def create_test_image(self) :
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        return SimpleUploadedFile('test_image.jpg', image_file.read(), content_type='image/jpeg')

    def test__photo_upload_success(self) :
        photographer = Photographer.objects.get(user=self.user)
        image = self.create_test_image()
        form_data = {'caption' :'Test photo caption', 'group' :self.group.id}
        response = self.client.post(reverse('photo-create'),{'image' :image, **form_data}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('photo-home'))
        photo = Photo.objects.filter(author=photographer).first()
        self.assertIsNotNone(photo)
        self.assertEqual(photo.caption, 'Test photo caption')
        self.assertEqual(photo.group, self.group)
        self.assertTrue(photo.image.name.startswith('photographer_pictures/test_image'))

        if os.path.exists(os.path.join(settings.MEDIA_ROOT, photo.image.name)) :
            os.remove(os.path.join(settings.MEDIA_ROOT, photo.image.name))

    def test__photo_upload__without_photographer_profile(self) :
        Photographer.objects.filter(user=self.user).delete()

        image = self.create_test_image()
        form_data = {'caption' :'Test photo caption', 'group' :self.group.id}
        response = self.client.post(reverse('photo-create'),{'image' :image, **form_data})

        self.assertFalse(Photo.objects.filter(caption='Test photo caption').exists())

    def test__photo_upload__unauthenticated(self) :
        self.client.logout()

        image = self.create_test_image()
        form_data = {'caption' :'Test photo caption', 'group' :self.group.id}

        response = self.client.post(reverse('photo-create'),{'image' :image, **form_data}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('accounts/login' in response.request['PATH_INFO'])
        self.assertFalse(Photo.objects.filter(caption='Test photo caption').exists())

    def test__photo_upload__invalid_form(self) :
        form_data = {'caption' :'Test photo caption', 'group' :self.group.id}

        response = self.client.post(reverse('photo-create'), form_data)

        self.assertFalse(Photo.objects.filter(caption='Test photo caption').exists())

from unittest import mock
from cloudinary import CloudinaryResource
from PIL.TiffImagePlugin import IFDRational
from photos.exif import extract_exif


def jpeg_with_exif(gps=True):
    image = Image.new('RGB', (64, 48), color='blue')
    exif = image.getexif()
    exif[0x010F] = 'Canon'
    exif[0x0110] = 'Canon EOS R6'
    sub = exif.get_ifd(0x8769)
    sub[0x829A] = IFDRational(1, 250)    # ExposureTime
    sub[0x829D] = IFDRational(28, 10)    # FNumber
    sub[0x8827] = 400                    # ISO
    sub[0x920A] = IFDRational(50, 1)     # FocalLength
    sub[0xA434] = 'RF50mm F1.8 STM'      # LensModel
    sub[0x9003] = '2024:05:17 18:42:05'  # DateTimeOriginal
    if gps:
        exif.get_ifd(0x8825)[2] = (IFDRational(42, 1), IFDRational(41, 1), IFDRational(0, 1))
    buf = io.BytesIO()
    image.save(buf, format='JPEG', exif=exif)
    return buf.getvalue()


class ExifExtractionTest(TestCase):
    def test_reads_display_fields_and_drops_gps(self):
        self.assertEqual(extract_exif(io.BytesIO(jpeg_with_exif())), {
            'camera': 'Canon EOS R6',
            'lens': 'RF50mm F1.8 STM',
            'exposure': '1/250 s',
            'aperture': 'f/2.8',
            'iso': '400',
            'focal_length': '50 mm',
            'taken_at': '17.05.2024 18:42',
        })

    def test_image_without_exif_and_non_image(self):
        buf = io.BytesIO()
        Image.new('RGB', (10, 10)).save(buf, format='PNG')
        self.assertEqual(extract_exif(buf), {})
        self.assertEqual(extract_exif(io.BytesIO(b'not an image')), {})


@mock.patch('cloudinary.models.uploader.upload_resource',
            return_value=CloudinaryResource('photos/test', format='jpg', version=1,
                                            type='upload', resource_type='image', metadata={}))
class PhotoSaveExifTest(TestCase):
    def setUp(self):
        user = UserModel.objects.create_user(username='exifuser', password='pw-12345678')
        self.photographer = Photographer.objects.get_or_create(user=user)[0]

    def test_exif_saved_on_upload_and_shown(self, upload):
        upload_file = SimpleUploadedFile('p.jpg', jpeg_with_exif(), content_type='image/jpeg')
        photo = Photo.objects.create(author=self.photographer, image=upload_file)
        upload.assert_called_once()
        photo.refresh_from_db()
        self.assertEqual(photo.exif['camera'], 'Canon EOS R6')
        self.assertNotIn('gps', str(photo.exif).lower())

        page = self.client.get(reverse('photo-detail', kwargs={'pk': photo.pk}))
        self.assertContains(page, '<strong>Камера:</strong> Canon EOS R6', html=True)
        self.assertContains(page, '<strong>Експонация:</strong> 1/250 s', html=True)

    def test_saving_without_new_file_keeps_exif(self, upload):
        photo = Photo.objects.create(author=self.photographer,
                                     image=SimpleUploadedFile('p.jpg', jpeg_with_exif(), content_type='image/jpeg'))
        photo = Photo.objects.get(pk=photo.pk)
        photo.caption = 'edited'
        photo.save()
        self.assertEqual(upload.call_count, 1)
        self.assertEqual(Photo.objects.get(pk=photo.pk).exif['iso'], '400')


@mock.patch('cloudinary.models.uploader.upload_resource',
            return_value=CloudinaryResource('photos/test', format='jpg', version=1,
                                            type='upload', resource_type='image', metadata={}))
class StarRatingTest(TestCase):
    def setUp(self):
        owner = UserModel.objects.create_user(username='owner', password='pw-12345678')
        self.photo = Photo.objects.create(
            author=Photographer.objects.get_or_create(user=owner)[0],
            image=SimpleUploadedFile('p.jpg', jpeg_with_exif(gps=False), content_type='image/jpeg'))
        self.url = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        self.rater = UserModel.objects.create_user(username='rater', password='pw-12345678')
        Photographer.objects.get_or_create(user=self.rater)

    def test_clicking_a_star_saves_and_lights_that_many(self, upload):
        self.client.force_login(self.rater)
        page = self.client.get(self.url)
        self.assertContains(page, 'class="star"', count=5)
        self.assertNotContains(page, 'is-on')

        self.client.post(reverse('photo-rate', kwargs={'pk': self.photo.pk}), {'score': '4'})
        self.assertEqual(self.photo.ratings.get().score, 4)
        page = self.client.get(self.url)
        self.assertContains(page, 'class="star is-on"', count=4)
        self.assertContains(page, 'title="Вашата оценка: 4"')

        # clicking another star changes the rating instead of adding one
        self.client.post(reverse('photo-rate', kwargs={'pk': self.photo.pk}), {'score': '2'})
        self.assertEqual(self.photo.ratings.get().score, 2)
        self.assertContains(self.client.get(self.url), 'class="star is-on"', count=2)

    def test_logged_out_sees_login_link(self, upload):
        page = self.client.get(self.url)
        self.assertContains(page, 'class="star-rating star-rating-static"')
        self.assertNotContains(page, 'name="score"')
