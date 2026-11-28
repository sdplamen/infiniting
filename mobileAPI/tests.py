import io
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from cloudinary import CloudinaryResource
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from articles.models import Article
from auctions.models import Auction, Bid
from groups.models import Group
from photos.models import Photo, Like, Comment, Rating

UserModel = get_user_model()

FAKE_UPLOAD = CloudinaryResource('photos/test', format='jpg', version=1,
                                 type='upload', resource_type='image', metadata={})


def jpeg(name='p.jpg'):
    buf = io.BytesIO()
    Image.new('RGB', (20, 20), color='gray').save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class ApiTestCase(APITestCase):
    """Base: two users with photographer profiles (made by the signal) and one photo by `owner`."""

    def setUp(self):
        self.owner = UserModel.objects.create_user(username='owner', password='pw-Strong-123')
        self.other = UserModel.objects.create_user(username='other', password='pw-Strong-123')
        self.staff = UserModel.objects.create_user(username='staff', password='pw-Strong-123', is_staff=True)
        # no real Cloudinary uploads in tests
        patcher = mock.patch('cloudinary.models.uploader.upload_resource', return_value=FAKE_UPLOAD)
        self.upload = patcher.start()
        self.addCleanup(patcher.stop)
        self.photo = Photo.objects.create(author=self.owner.photographer, image=jpeg(), caption='mine')


class AuthApiTest(ApiTestCase):
    def test_register_login_and_use_token(self):
        r = self.client.post(reverse('register-api'), {'username': 'newbie', 'password': 'pw-Strong-123'})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(UserModel.objects.get(username='newbie').photographer)

        r = self.client.post(reverse('token_obtain_pair'), {'username': 'newbie', 'password': 'pw-Strong-123'})
        self.assertEqual(r.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        self.assertEqual(self.client.get(reverse('rating-list-create')).status_code, 200)

    def test_register_rejects_weak_password(self):
        r = self.client.post(reverse('register-api'), {'username': 'weak', 'password': '123'})
        self.assertEqual(r.status_code, 400)
        self.assertFalse(UserModel.objects.filter(username='weak').exists())


class PhotoApiTest(ApiTestCase):
    def test_anyone_can_list_with_counts(self):
        Like.objects.create(user=self.other, photo=self.photo)
        Rating.objects.create(user=self.other.photographer, photo=self.photo, score=4)
        Rating.objects.create(user=self.staff.photographer, photo=self.photo, score=2)
        r = self.client.get(reverse('photo-list-create'))
        self.assertEqual(r.status_code, 200)
        item = r.data[0]
        self.assertEqual(item['author']['username'], 'owner')
        self.assertEqual(item['likes_count'], 1)
        self.assertEqual(item['average_rating'], 3.0)
        self.assertTrue(item['image_url'])

    def test_logged_in_user_uploads_photo(self):
        self.client.force_authenticate(self.other)
        r = self.client.post(reverse('photo-list-create'), {'image': jpeg(), 'caption': 'new'}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Photo.objects.get(pk=r.data['id']).author, self.other.photographer)
        self.assertEqual(r.data['likes_count'], 0)

    def test_upload_requires_image_and_login(self):
        self.assertEqual(self.client.post(reverse('photo-list-create'), {'caption': 'x'}).status_code, 401)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(reverse('photo-list-create'), {'caption': 'x'}).status_code, 400)

    def test_upload_to_hidden_group_rejected(self):
        hidden = Group.objects.create(name='Hidden', author=self.owner)  # unapproved, other isn't a member
        self.client.force_authenticate(self.other)
        r = self.client.post(reverse('photo-list-create'), {'image': jpeg(), 'group': hidden.pk}, format='multipart')
        self.assertEqual(r.status_code, 400)

    def test_only_author_edits_or_deletes(self):
        url = reverse('photo-detail-api', kwargs={'pk': self.photo.pk})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(url, {'caption': 'hacked'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {'caption': 'edited'}).status_code, 200)
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.caption, 'edited')
        self.assertEqual(self.client.delete(url).status_code, 204)


class LikeCommentRatingApiTest(ApiTestCase):
    def test_like_once_and_unlike(self):
        self.client.force_authenticate(self.other)
        r = self.client.post(reverse('like-list-create'), {'photo': self.photo.pk})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.client.post(reverse('like-list-create'), {'photo': self.photo.pk}).status_code, 400)
        self.assertEqual(len(self.client.get(reverse('like-list-create')).data), 1)

        like_url = reverse('like-detail', kwargs={'pk': r.data['id']})
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(like_url).status_code, 403)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(like_url).status_code, 204)

    def test_photo_likes_are_listed_by_photo(self):
        Like.objects.create(user=self.other, photo=self.photo)
        r = self.client.get(reverse('like-list-create'), {'photo': self.photo.pk})
        self.assertEqual([like['user']['username'] for like in r.data], ['other'])

    def test_comments(self):
        self.client.force_authenticate(self.other)
        r = self.client.post(reverse('comment-list-create'), {'photo': self.photo.pk, 'text': 'Nice'})
        self.assertEqual(r.status_code, 201, r.data)
        url = reverse('comment-detail', kwargs={'pk': r.data['id']})
        self.assertEqual(self.client.patch(url, {'text': 'Very nice'}).status_code, 200)

        # the photo's author can't edit someone's comment but may remove it
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {'text': 'Bad'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 204)

        comment = Comment.objects.create(user=self.other, photo=self.photo, text='x')
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(reverse('comment-detail', kwargs={'pk': comment.pk})).status_code, 403)

    def test_rating_once_then_update(self):
        self.client.force_authenticate(self.other)
        r = self.client.post(reverse('rating-list-create'), {'photo': self.photo.pk, 'score': 5})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.client.post(reverse('rating-list-create'), {'photo': self.photo.pk, 'score': 3}).status_code, 400)
        self.assertEqual(self.client.post(reverse('rating-list-create'), {'photo': self.photo.pk, 'score': 9}).status_code, 400)

        url = reverse('rating-detail', kwargs={'pk': r.data['id']})
        self.assertEqual(self.client.patch(url, {'score': 2}).status_code, 200)
        self.assertEqual(Rating.objects.get(pk=r.data['id']).score, 2)

        # other people's ratings are private
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(reverse('rating-list-create')).data, [])


class ArticleApiTest(ApiTestCase):
    def test_create_goes_to_approval(self):
        self.client.force_authenticate(self.other)
        r = self.client.post(reverse('article-list-create'), {'title': 'T', 'content': 'C', 'is_approved': True})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(r.data['is_approved'])
        self.assertEqual(Article.objects.get(pk=r.data['id']).author, self.other.photographer)

    def test_unapproved_visible_only_to_author(self):
        draft = Article.objects.create(title='Draft', content='x', author=self.owner.photographer)
        Article.objects.create(title='Live', content='x', author=self.owner.photographer, is_approved=True)
        self.assertEqual([a['title'] for a in self.client.get(reverse('article-list-create')).data], ['Live'])
        self.client.force_authenticate(self.owner)
        self.assertEqual(len(self.client.get(reverse('article-list-create')).data), 2)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse('article-detail-api', kwargs={'pk': draft.pk})).status_code, 404)

    def test_only_author_edits(self):
        article = Article.objects.create(title='T', content='x', author=self.owner.photographer, is_approved=True)
        url = reverse('article-detail-api', kwargs={'pk': article.pk})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(url, {'title': 'Mine now'}).status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {'title': 'New'}).status_code, 200)


class AuctionBidApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        now = timezone.now()
        self.auction = Auction.objects.create(photo=self.photo, start_time=now - timedelta(hours=1),
                                              end_time=now + timedelta(days=1), starting_bid=Decimal('10.00'))

    def bid(self, amount, auction=None):
        return self.client.post(reverse('bid-list-create'),
                                {'auction': (auction or self.auction).pk, 'amount': amount})

    def test_only_staff_creates_auctions(self):
        photo = Photo.objects.create(author=self.owner.photographer, image=jpeg())
        now = timezone.now()
        data = {'photo': photo.pk, 'start_time': now.isoformat(),
                'end_time': (now + timedelta(days=2)).isoformat(), 'starting_bid': '5.00'}
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(reverse('auction-list-create'), data).status_code, 403)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(reverse('auction-list-create'), data).status_code, 201)

        bad = {**data, 'end_time': (now - timedelta(days=1)).isoformat()}
        self.assertEqual(self.client.post(reverse('auction-list-create'), bad).status_code, 400)

    def test_bid_updates_auction(self):
        self.client.force_authenticate(self.other)
        r = self.bid('15.00')
        self.assertEqual(r.status_code, 201, r.data)
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_highest_bid, Decimal('15.00'))
        self.assertEqual(self.auction.highest_bidder, self.other)
        self.assertEqual(Bid.objects.get().bidder, self.other)
        self.assertEqual(len(self.client.get(reverse('bid-list-create')).data), 1)

    def test_bid_rules(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.bid('10.00').status_code, 400)  # not above the starting bid
        self.assertEqual(self.bid('20.00').status_code, 201)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.bid('20.00').status_code, 400)  # not above the highest bid
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.bid('50.00').status_code, 400)  # own photo

    def test_no_bids_on_closed_or_future_auctions(self):
        self.client.force_authenticate(self.other)
        self.auction.is_active = False
        self.auction.save()
        self.assertEqual(self.bid('50.00').status_code, 400)
        self.auction.is_active = True
        self.auction.start_time = timezone.now() + timedelta(hours=1)
        self.auction.save()
        self.assertEqual(self.bid('50.00').status_code, 400)
        self.assertFalse(Bid.objects.exists())

    def test_bids_are_final_and_private(self):
        self.client.force_authenticate(self.other)
        bid_id = self.bid('15.00').data['id']
        url = reverse('bid-detail', kwargs={'pk': bid_id})
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.patch(url, {'amount': '1.00'}).status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(url).status_code, 404)


class GroupApiTest(ApiTestCase):
    def test_create_join_leave(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post(reverse('group-list-create'), {'name': 'Street', 'is_approved': True})
        self.assertEqual(r.status_code, 201, r.data)
        group = Group.objects.get(pk=r.data['id'])
        self.assertEqual(group.author, self.owner)
        self.assertFalse(group.is_approved)
        self.assertIn(self.owner, group.members.all())

        group.is_approved = True
        group.save()
        url = reverse('group-membership-api', kwargs={'pk': group.pk})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertIn(self.other, group.members.all())
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertNotIn(self.other, group.members.all())

    def test_unapproved_group_hidden(self):
        group = Group.objects.create(name='Pending', author=self.owner)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(reverse('group-list-create')).data, [])
        self.assertEqual(self.client.get(reverse('group-detail-api', kwargs={'pk': group.pk})).status_code, 404)
        self.assertEqual(self.client.post(reverse('group-membership-api', kwargs={'pk': group.pk})).status_code, 404)

    def test_author_or_staff_edits(self):
        group = Group.objects.create(name='G', author=self.owner, is_approved=True)
        url = reverse('group-detail-api', kwargs={'pk': group.pk})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(url, {'description': 'x'}).status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {'description': 'mine'}).status_code, 200)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(url).status_code, 204)
