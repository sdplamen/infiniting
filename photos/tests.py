from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from photos.models import Photo
from photos.views import PhotoCreateView
from users.models import Photographer
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.http import HttpRequest
import os

User = get_user_model()

class TestPhotoCreateView(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.create_url = reverse('photo-create')
        self.success_url = reverse('photo-home')

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

        os.remove(expected_path)

