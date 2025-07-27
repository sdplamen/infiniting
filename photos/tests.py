import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.conf import settings
from articles.models import Photographer
from photos.models import Photo
from photos.views import PhotoCreateView

User = get_user_model()

class TestPhotoCreateView(TestCase):
    def setUp(self):
        self._original_media_root = settings.MEDIA_ROOT
        self._original_media_url = settings.MEDIA_URL

        self.test_media_root = os.path.join(settings.BASE_DIR, 'test_media')
        if not os.path.exists(self.test_media_root):
            os.makedirs(self.test_media_root)

        settings.MEDIA_ROOT = self.test_media_root
        settings.MEDIA_URL = '/test_media/'

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.create_url = reverse('photo-create')
        self.success_url = reverse('photo-home')

    def _delete_directory_contents(self, path):
        if not os.path.exists(path):
            return

        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            if os.path.isfile(entry_path):
                os.remove(entry_path)
            elif os.path.isdir(entry_path):
                self._delete_directory_contents(entry_path)
                os.rmdir(entry_path)

    def tearDown(self):
        self._delete_directory_contents(self.test_media_root)
        if os.path.exists(self.test_media_root):
            os.rmdir(self.test_media_root)

        settings.MEDIA_ROOT = self._original_media_root
        settings.MEDIA_URL = self._original_media_url

    def _create_user_and_photographer(self, user_id):
        username = f'test_user_{user_id}'
        email = f'test_email_{user_id}@example.com'
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpassword'
        )
        photographer, created = Photographer.objects.get_or_create(user=user)
        return user, photographer

    def test_photo_upload_success(self):
        user, photographer = self._create_user_and_photographer(1)

        image_content = b'GIF89a\x01\x00\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;'
        uploaded_image = SimpleUploadedFile("test_image.png", image_content, content_type="image/png")

        request = HttpRequest()
        request.method = 'POST'
        request.user = user
        request.FILES = {'image': uploaded_image,}
        request.POST = {'caption': 'My Test Photo', 'description': 'A description for my test photo.',}

        request.META['SERVER_NAME'] = 'testserver'
        request.META['SERVER_PORT'] = '80'
        request.META['HTTP_HOST'] = 'testserver'
        request.path = self.create_url

        response = PhotoCreateView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.success_url)
        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.caption, 'My Test Photo')
        self.assertEqual(photo.author, photographer)
        self.assertIn('test_image', photo.image.name)
        self.assertTrue(photo.image.name.endswith('.png'))

        expected_path = os.path.join(settings.MEDIA_ROOT, photo.image.name)
        self.assertTrue(os.path.exists(expected_path))