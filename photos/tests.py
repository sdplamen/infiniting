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


class PhotoListTitleLinkTest(TestCase):
    def test_title_links_to_photo_detail(self):
        author = Photographer.objects.get_or_create(
            user=UserModel.objects.create_user(username='shooter', password='pw-12345678'))[0]
        photo = Photo.objects.create(author=author, image='dummy_image.jpg', caption='Залез')
        detail_url = reverse('photo-detail', kwargs={'pk': photo.pk})

        page = self.client.get(reverse('photo-home'))
        self.assertContains(page, f'<a href="{detail_url}" class="image-link"')
        self.assertNotContains(page, 'onclick="window.location.href')
        self.assertContains(page, f'<a href="{detail_url}" class="title-link"')
        self.assertContains(page, '<strong>Залез</strong>')
        self.assertNotContains(page, 'Виж детайли</a>')


class PhotoDetailLinksTest(TestCase):
    def setUp(self):
        author = Photographer.objects.get_or_create(
            user=UserModel.objects.create_user(username='snap', password='pw-12345678'))[0]
        self.photo = Photo.objects.create(author=author, image='dummy_image.jpg', caption='Мост')
        self.url = reverse('photo-detail', kwargs={'pk': self.photo.pk})

    def test_photo_is_a_link_to_full_size(self):
        page = self.client.get(self.url)
        self.assertContains(page, f'<a href="{reverse("photo-full-photo", args=[self.photo.pk])}" class="image-link"')
        self.assertNotContains(page, 'onclick="window.location.href')

    def test_logged_out_like_is_login_link(self):
        page = self.client.get(self.url)
        self.assertContains(page, f'<a href="{reverse("login")}" class="icon-like-toggle like-login-link"')
        self.assertNotContains(page, 'Влезте, за да харесате</a>')


class PhotoListOwnerIconsTest(TestCase):
    def setUp(self):
        self.me = UserModel.objects.create_user(username='me-photo', password='pw-12345678')
        other = UserModel.objects.create_user(username='other-photo', password='pw-12345678')
        self.mine = Photo.objects.create(author=Photographer.objects.get_or_create(user=self.me)[0], image='dummy_image.jpg')
        self.theirs = Photo.objects.create(author=Photographer.objects.get_or_create(user=other)[0], image='dummy_image.jpg')

    def test_icons_only_on_own_photos(self):
        self.client.force_login(self.me)
        page = self.client.get(reverse('photo-home'))
        self.assertContains(page, f'href="{reverse("photo-edit", kwargs={"pk": self.mine.pk})}" class="owner-action owner-action-edit"')
        self.assertContains(page, f'href="{reverse("photo-delete", kwargs={"pk": self.mine.pk})}" class="owner-action owner-action-delete"')
        self.assertNotContains(page, reverse('photo-edit', kwargs={'pk': self.theirs.pk}))
        self.assertContains(page, 'card-owner-actions', count=1)

    def test_logged_out_sees_no_icons(self):
        self.assertNotContains(self.client.get(reverse('photo-home')), 'owner-action')


from photos.models import Comment


class CommentDeleteTest(TestCase):
    def setUp(self):
        self.owner = UserModel.objects.create_user(username='p-owner', password='pw-12345678')
        self.writer = UserModel.objects.create_user(username='c-writer', password='pw-12345678')
        self.stranger = UserModel.objects.create_user(username='stranger', password='pw-12345678')
        self.photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=self.owner)[0], image='dummy_image.jpg')
        Photographer.objects.get_or_create(user=self.writer)

    def _comment(self):
        return Comment.objects.create(user=self.writer, photo=self.photo, text='Хубаво!')

    def _url(self, comment):
        return reverse('photo-comment-delete', kwargs={'pk': self.photo.pk, 'comment_pk': comment.pk})

    def test_writer_and_photo_owner_can_delete(self):
        for user in (self.writer, self.owner):
            comment = self._comment()
            self.client.force_login(user)
            response = self.client.post(self._url(comment))
            self.assertRedirects(response, reverse('photo-detail', kwargs={'pk': self.photo.pk}))
            self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_others_get_403_and_get_is_refused(self):
        comment = self._comment()
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(self._url(comment)).status_code, 403)
        self.client.force_login(self.writer)
        self.assertEqual(self.client.get(self._url(comment)).status_code, 405)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_bin_shown_to_writer_and_owner_only(self):
        comment = self._comment()
        detail = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        for user, visible in ((self.writer, True), (self.owner, True), (self.stranger, False)):
            self.client.force_login(user)
            (self.assertContains if visible else self.assertNotContains)(self.client.get(detail), self._url(comment))


class PhotoCommentFormLookTest(TestCase):
    def test_label_and_size_match_other_comment_forms(self):
        viewer = UserModel.objects.create_user(username='look', password='pw-12345678')
        photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=viewer)[0], image='dummy_image.jpg')
        self.client.force_login(viewer)
        page = self.client.get(reverse('photo-detail', kwargs={'pk': photo.pk}))
        self.assertContains(page, '>Коментар:</label>')
        self.assertContains(page, 'rows="3"')


class BackLinksTest(TestCase):
    """Detail pages have no 'Към всички …' back links; form links are text links."""
    def test_no_back_links_on_photo_article_and_auction_pages(self):
        from datetime import timedelta
        from django.utils import timezone
        from articles.models import Article
        from auctions.models import Auction
        author = Photographer.objects.get_or_create(user=UserModel.objects.create_user(username='back', password='pw-12345678'))[0]
        photo = Photo.objects.create(author=author, image='dummy_image.jpg')
        article = Article.objects.create(title='т', content='с', author=author, is_approved=True)
        now = timezone.now()
        auction = Auction.objects.create(photo=photo, start_time=now, end_time=now + timedelta(days=1), starting_bid=1)
        for page_url, list_url, label in (
                (reverse('photo-detail', kwargs={'pk': photo.pk}), reverse('photo-home'), 'Към всички снимки'),
                (reverse('article-detail', kwargs={'pk': article.pk}), reverse('article-list'), 'Към всички статии'),
                (reverse('auction-detail', kwargs={'pk': auction.pk}), reverse('auction-list'), 'Към всички аукциони')):
            page = self.client.get(page_url)
            self.assertNotContains(page, label)  # removed: the bottom nav bar links to every list
            self.assertNotContains(page, 'class="back-link"')
            self.assertContains(page, f'href="{list_url}"')  # still reachable via the nav bar

    def test_cancel_is_a_text_link_on_edit_and_delete_pages(self):
        from articles.models import Article
        from groups.models import Group
        owner = UserModel.objects.create_user(username='canceller', password='pw-12345678')
        author = Photographer.objects.get_or_create(user=owner)[0]
        photo = Photo.objects.create(author=author, image='dummy_image.jpg')
        article = Article.objects.create(title='т', content='с', author=author, is_approved=True)
        group = Group.objects.create(name='Г', author=owner, is_approved=True)
        self.client.force_login(owner)
        pages = {
            'photo-edit': (photo.pk, 'photo-detail'), 'photo-delete': (photo.pk, 'photo-detail'),
            'article-edit': (article.pk, 'article-detail'), 'article-delete': (article.pk, 'article-detail'),
            'group-edit': (group.pk, 'group-detail'), 'group-delete': (group.pk, 'group-detail'),
            'user-profile-edit': (author.pk, 'user-profile-detail'), 'user-profile-delete': (author.pk, 'user-profile-detail'),
        }
        for name, (pk, back) in pages.items():
            page = self.client.get(reverse(name, kwargs={'pk': pk}))
            back_url = reverse(back, kwargs={'pk': pk})
            # icons only, text in the hover hint: ✓ save on edit pages, bin on delete pages, ✕ cancel on both
            if name.endswith('-edit'):
                self.assertContains(page, '<button type="submit" class="owner-action owner-action-save" title="Запази промените" aria-label="Запази промените"><i class="fas fa-check"></i></button>', html=True, msg_prefix=name)
            else:
                self.assertContains(page, '<button type="submit" class="owner-action owner-action-delete" title="Да, изтрий" aria-label="Да, изтрий"><i class="fas fa-trash-alt"></i></button>', html=True, msg_prefix=name)
            self.assertContains(page, f'<a href="{back_url}" class="owner-action owner-action-cancel" title="Откажи" aria-label="Откажи"><i class="fas fa-times"></i></a>', html=True, msg_prefix=name)
            self.assertNotContains(page, 'class="cancel-link"', msg_prefix=name)

    def test_comment_login_links_return_to_the_same_page(self):
        from datetime import timedelta
        from django.utils import timezone
        from urllib.parse import quote
        from articles.models import Article
        from auctions.models import Auction
        from groups.models import Group
        user = UserModel.objects.create_user(username='logger', password='pw-12345678')
        author = Photographer.objects.get_or_create(user=user)[0]
        photo = Photo.objects.create(author=author, image='dummy_image.jpg')
        now = timezone.now()
        pages = [
            reverse('photo-detail', kwargs={'pk': photo.pk}),
            reverse('article-detail', kwargs={'pk': Article.objects.create(title='т', content='с', author=author, is_approved=True).pk}),
            reverse('group-detail', kwargs={'pk': Group.objects.create(name='Г2', author=user, is_approved=True).pk}),
            reverse('auction-detail', kwargs={'pk': Auction.objects.create(photo=photo, start_time=now, end_time=now + timedelta(days=1), starting_bid=1).pk}),
            reverse('user-profile-detail', kwargs={'pk': author.pk}),
        ]
        for url in pages:
            login_url = f'{reverse("login")}?next={quote(url)}'
            page = self.client.get(url)
            self.assertContains(page, f'href="{login_url}" class="login-link"', msg_prefix=url)
            self.assertNotContains(page, 'class="custom-button small-text">Влезте', msg_prefix=url)

        # signing in through the link lands back on the page
        response = self.client.post(f'{reverse("login")}?next={quote(pages[0], safe="")}', {'username': 'logger', 'password': 'pw-12345678'})
        self.assertRedirects(response, pages[0])


class AddCommentTextButtonTest(TestCase):
    def test_add_comment_is_a_text_button(self):
        user = UserModel.objects.create_user(username='commenter', password='pw-12345678')
        photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=user)[0], image='dummy_image.jpg')
        self.client.force_login(user)
        page = self.client.get(reverse('photo-detail', kwargs={'pk': photo.pk}))
        self.assertContains(page, '<button type="submit" class="text-button"><i class="fas fa-paper-plane me-1"></i>Добави коментар</button>', html=True)
        self.assertNotContains(page, 'full-width">Добави коментар')


class CreateLinksAndButtonsTest(TestCase):
    def test_list_create_links_and_create_form_buttons(self):
        staff = UserModel.objects.create_user(username='creator', password='pw-12345678', is_staff=True)
        Photographer.objects.get_or_create(user=staff)
        self.client.force_login(staff)
        for list_name, create_name, label in (('photo-home', 'photo-create', 'Качи снимка'),
                                              ('article-list', 'article-create', 'Създай нова статия'),
                                              ('group-list', 'group-create', 'Създай нова група'),
                                              ('auction-list', 'auction-create', 'Създай нов аукцион')):
            page = self.client.get(reverse(list_name))
            self.assertContains(page, f'href="{reverse(create_name)}" class="create-link"', msg_prefix=list_name)
            self.assertContains(page, label, msg_prefix=list_name)
        for create_name, label in (('photo-create', 'Качи снимка'), ('article-create', 'Публикувай статията'),
                                   ('group-create', 'Създай група'), ('auction-create', 'Създай аукциона')):
            page = self.client.get(reverse(create_name))
            self.assertContains(page, 'class="text-button text-button-success"', msg_prefix=create_name)
            self.assertContains(page, f'{label}</button>', msg_prefix=create_name)
            self.assertNotContains(page, 'custom-button-primary full-width', msg_prefix=create_name)
