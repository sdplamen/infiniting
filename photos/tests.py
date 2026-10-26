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