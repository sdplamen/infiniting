"""
N+1 guard: every list and detail page must run the same number of SQL queries
whether the site holds a little data or a lot. Each test measures a page,
adds more of everything (photographers, photos, likes, comments, ratings,
follows, groups, articles, bids, essays) and measures again.

A failure names the page and both counts. To see which query repeats, open the
page with django-debug-toolbar (see readme.md) and check its SQL panel.
"""
from datetime import timedelta
from itertools import count

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from articles.models import Article, ArticleComment
from auctions.models import Auction, AuctionComment, Bid
from essays.models import Essay
from groups.models import Group, GroupComment
from photos.models import Comment, Like, Photo, Rating
from users.models import Follow, ProfileComment

UserModel = get_user_model()
_ids = count()


class QueryCountTest(TestCase):
    """`owner` is the photographer whose profile, group, auction and essay the
    detail pages show; `add_people(n)` adds n more photographers around them."""

    def setUp(self):
        self.owner = UserModel.objects.create_user(f'owner{next(_ids)}', password=None)
        self.group = Group.objects.create(name=f'group{next(_ids)}', author=self.owner, is_approved=True)
        self.group.members.add(self.owner)
        now = timezone.now()
        self.photo = self._photo(self.owner, self.group)
        self.auction = Auction.objects.create(photo=self.photo, start_time=now - timedelta(hours=1),
                                              end_time=now + timedelta(days=1), starting_bid=1)
        self.article = Article.objects.create(title='a', content='x', author=self.owner.photographer, is_approved=True)
        self.essay = Essay.objects.create(author=self.owner.photographer, title='e', is_published=True)
        self.essay.append_photos([self.photo])
        self.add_people(3)                  # 7 photos: enough for a second feed page

    def _photo(self, user, group=None):
        return Photo.objects.create(author=user.photographer, image=f'photos/p{next(_ids)}', caption='p', group=group)

    def add_people(self, n):
        now = timezone.now()
        for _ in range(n):
            user = UserModel.objects.create_user(f'u{next(_ids)}', password=None)
            group = Group.objects.create(name=f'group{next(_ids)}', author=user, is_approved=True)
            group.members.add(user, self.owner)
            self.group.members.add(user)
            own = self._photo(user, group)
            owners = self._photo(self.owner, self.group)
            for photo in (own, owners, self.photo):
                Like.objects.create(user=user, photo=photo)
                Comment.objects.create(user=user, photo=photo, text='c')
                Rating.objects.create(user=user.photographer, photo=photo, score=4)
            Follow.objects.create(follower=user, followed=self.owner)
            Follow.objects.create(follower=self.owner, followed=user)
            ProfileComment.objects.create(user=user, photographer=self.owner.photographer, text='c')
            GroupComment.objects.create(user=user, group=self.group, text='c')
            article = Article.objects.create(title='a', content='x', author=user.photographer, is_approved=True)
            ArticleComment.objects.create(user=user, article=self.article, text='c')
            ArticleComment.objects.create(user=self.owner, article=article, text='c')
            amount = self.auction.current_highest_bid + 1
            Bid.objects.create(auction=self.auction, bidder=user, amount=amount)
            Auction.objects.filter(pk=self.auction.pk).update(current_highest_bid=amount, highest_bidder=user)
            AuctionComment.objects.create(auction=self.auction, user=user, text='c')
            Auction.objects.create(photo=own, start_time=now - timedelta(hours=1),
                                   end_time=now + timedelta(days=1), starting_bid=1)
            essay = Essay.objects.create(author=user.photographer, title='e', is_published=True)
            essay.append_photos([own, owners])
            self.essay.append_photos([owners])

    def queries(self, path, api=False):
        # a fresh user object each time: Django caches permissions on the instance
        user = UserModel.objects.get(pk=self.owner.pk)
        client = self.client
        if api:
            client = APIClient()
            client.force_authenticate(user)
        else:
            client.force_login(user)
        with CaptureQueriesContext(connection) as ctx:
            response = client.get(path)
        self.assertEqual(response.status_code, 200, path)
        return len(ctx.captured_queries)

    def assertFlat(self, path, api=False):
        before = self.queries(path, api)
        self.add_people(8)
        after = self.queries(path, api)
        self.assertEqual(before, after, f'{path}: {before} queries with little data, {after} with more (N+1)')

    # --- pages ---------------------------------------------------------------------

    def test_home_feed(self):
        self.assertFlat('/')

    def test_home_feed_later_page(self):
        self.assertFlat('/?page=2')

    def test_photo_detail(self):
        self.assertFlat(f'/{self.photo.pk}/photo-detail/')

    def test_lightbox(self):
        self.assertFlat(f'/{self.photo.pk}/full-photo/?essay={self.essay.pk}')

    def test_profile_list(self):
        self.assertFlat('/users/')

    def test_profile_detail(self):
        self.assertFlat(f'/users/{self.owner.photographer.pk}/')

    def test_group_list(self):
        self.assertFlat('/groups/')

    def test_group_detail(self):
        self.assertFlat(f'/groups/{self.group.pk}/')

    def test_auction_list(self):
        for sort in ('latest', 'rating', 'likes'):
            with self.subTest(sort=sort):
                self.assertFlat(f'/auctions/?sort_by={sort}')

    def test_auction_detail(self):
        self.assertFlat(f'/auctions/{self.auction.pk}/')

    def test_article_list(self):
        self.assertFlat('/articles/')

    def test_article_detail(self):
        self.assertFlat(f'/articles/{self.article.pk}/')

    def test_essay_list(self):
        self.assertFlat('/essays/')

    def test_essay_detail(self):
        self.assertFlat(f'/essays/{self.essay.pk}/')

    def test_essay_sequence_editor(self):
        self.assertFlat(f'/essays/{self.essay.pk}/sequence/')

    # --- API -------------------------------------------------------------------------

    def test_api_lists(self):
        for path in ('/api/photos/', f'/api/comments/?photo={self.photo.pk}', f'/api/likes/?photo={self.photo.pk}',
                     '/api/articles/', '/api/auctions/', '/api/groups/', '/api/bids/', '/api/ratings/'):
            with self.subTest(path=path):
                self.assertFlat(path, api=True)
