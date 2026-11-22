from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone
from auctions.models import Auction
from photos.models import Photo
from users.models import Photographer

# Create your tests here.
User = get_user_model()

class TestPaymentView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testname', password='testpass')
        self.photographer, created = Photographer.objects.get_or_create(user=self.user)
        self.photo = Photo.objects.create(author=self.photographer, image='dummy_image.jpg')
        self.auction = Auction.objects.create(
            photo=self.photo,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            starting_bid=10.00,
            current_highest_bid=50.00,
            highest_bidder=self.user,
            is_active=False
        )

    def test__payment_view__accessible_by_winner(self):
        self.client.login(username='testname', password='testpass')
        response = self.client.get(reverse('auction-payment', kwargs={'pk': self.auction.pk}))
        self.assertEqual(response.status_code, 200)

class AuctionListTitleLinkTest(TestCase):
    def test_title_links_to_auction_and_no_details_button(self):
        author = Photographer.objects.get_or_create(user=User.objects.create_user(username='seller', password='pw-12345678'))[0]
        photo = Photo.objects.create(author=author, image='dummy_image.jpg', caption='Мъгла')
        now = timezone.now()
        auction = Auction.objects.create(photo=photo, start_time=now, end_time=now + timedelta(days=1), starting_bid=10)
        detail_url = reverse('auction-detail', kwargs={'pk': auction.pk})

        page = self.client.get(reverse('auction-list'))
        self.assertContains(page, f'<a href="{detail_url}" class="image-link"')
        self.assertNotContains(page, 'onclick="window.location.href')
        self.assertContains(page, f'<a href="{detail_url}" class="title-link"')
        self.assertContains(page, 'Аукцион за <strong>Мъгла</strong>')
        self.assertNotContains(page, 'Виж детайли и направи оферта.')


class AuctionDetailPageTest(TestCase):
    def setUp(self):
        seller = User.objects.create_user(username='seller2', password='pw-12345678')
        author = Photographer.objects.get_or_create(user=seller)[0]
        self.photo = Photo.objects.create(author=author, image='dummy_image.jpg', caption='Река')
        now = timezone.now()
        self.auction = Auction.objects.create(photo=self.photo, start_time=now - timedelta(hours=1),
                                              end_time=now + timedelta(days=1), starting_bid=10)
        self.url = reverse('auction-detail', kwargs={'pk': self.auction.pk})

    def test_title_and_photo_links(self):
        page = self.client.get(self.url)
        self.assertContains(page, f'<a href="{reverse("photo-detail", kwargs={"pk": self.photo.pk})}" class="title-link"')
        self.assertContains(page, f'<a href="{reverse("photo-full-photo", args=[self.photo.pk])}" class="image-link"')

    def test_staff_sees_deactivate_icon_with_confirm(self):
        self.client.force_login(User.objects.create_user(username='boss', password='pw-12345678', is_staff=True))
        page = self.client.get(self.url)
        self.assertContains(page, f'<form method="POST" action="{reverse("auction-deactivate", kwargs={"pk": self.auction.pk})}"')
        self.assertContains(page, "confirm('Деактивирай аукциона?')")
        self.assertNotContains(page, 'Деактивирай аукциона</a>')

    def test_bid_button_text(self):
        self.client.force_login(User.objects.create_user(username='bidder', password='pw-12345678'))
        page = self.client.get(self.url)
        self.assertNotContains(page, 'оферta')


class AuctionListStaffIconTest(TestCase):
    def setUp(self):
        author = Photographer.objects.get_or_create(user=User.objects.create_user(username='s3', password='pw-12345678'))[0]
        now = timezone.now()
        self.auction = Auction.objects.create(photo=Photo.objects.create(author=author, image='dummy_image.jpg'),
                                              start_time=now, end_time=now + timedelta(days=1), starting_bid=5)
        self.deactivate_url = reverse('auction-deactivate', kwargs={'pk': self.auction.pk})

    def test_no_deactivate_icon_on_cards_but_on_auction_page(self):
        self.client.force_login(User.objects.create_user(username='st', password='pw-12345678', is_staff=True))
        self.assertNotContains(self.client.get(reverse('auction-list')), self.deactivate_url)
        page = self.client.get(reverse('auction-detail', kwargs={'pk': self.auction.pk}))
        self.assertContains(page, f'<form method="POST" action="{self.deactivate_url}"')
        self.assertContains(page, "confirm('Деактивирай аукциона?')")

from auctions.models import AuctionComment


class AuctionCommentsTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='au-seller', password='pw-12345678')
        self.writer = User.objects.create_user(username='au-writer', password='pw-12345678')
        self.staff = User.objects.create_user(username='au-staff', password='pw-12345678', is_staff=True)
        Photographer.objects.get_or_create(user=self.writer)
        photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=self.seller)[0], image='dummy_image.jpg')
        now = timezone.now()
        self.auction = Auction.objects.create(photo=photo, start_time=now, end_time=now + timedelta(days=1), starting_bid=5)
        self.detail = reverse('auction-detail', kwargs={'pk': self.auction.pk})

    def _comment(self):
        return AuctionComment.objects.create(user=self.writer, auction=self.auction, text='Колко струва доставката?')

    def _delete_url(self, comment):
        return reverse('auction-comment-delete', kwargs={'pk': self.auction.pk, 'comment_pk': comment.pk})

    def test_signed_in_user_adds_comment_and_sees_it(self):
        self.client.force_login(self.writer)
        response = self.client.post(reverse('auction-comment', kwargs={'pk': self.auction.pk}), {'text': 'Интересно'})
        self.assertRedirects(response, self.detail)
        self.assertEqual(AuctionComment.objects.get().user, self.writer)
        page = self.client.get(self.detail)
        self.assertContains(page, 'Интересно')
        self.assertContains(page, 'Коментари (1)')

    def test_logged_out_and_empty_are_rejected(self):
        self.client.post(reverse('auction-comment', kwargs={'pk': self.auction.pk}), {'text': 'x'})
        self.assertContains(self.client.get(self.detail), 'Влезте, за да добавяте коментари')
        self.client.force_login(self.writer)
        self.client.post(reverse('auction-comment', kwargs={'pk': self.auction.pk}), {'text': ''})
        self.assertFalse(AuctionComment.objects.exists())

    def test_comments_closed_after_end_or_deactivation(self):
        comment_url = reverse('auction-comment', kwargs={'pk': self.auction.pk})
        self._comment()
        self.client.force_login(self.writer)
        for change in ({'end_time': timezone.now() - timedelta(minutes=1)}, {'is_active': False}):
            Auction.objects.filter(pk=self.auction.pk).update(**{'end_time': timezone.now() + timedelta(days=1), 'is_active': True, **change})
            self.assertEqual(self.client.post(comment_url, {'text': 'Късно'}).status_code, 403)
            page = self.client.get(self.detail)
            self.assertContains(page, 'Аукционът е приключил. Коментарите са затворени.')
            self.assertNotContains(page, f'action="{comment_url}"')
            self.assertContains(page, 'Колко струва доставката?')  # old comments stay readable
        self.assertEqual(AuctionComment.objects.count(), 1)

    def test_writer_and_staff_can_delete(self):
        for user in (self.writer, self.staff):
            comment = self._comment()
            self.client.force_login(user)
            self.assertRedirects(self.client.post(self._delete_url(comment)), self.detail)
            self.assertFalse(AuctionComment.objects.filter(pk=comment.pk).exists())

    def test_seller_cannot_delete_and_get_is_refused(self):
        comment = self._comment()
        self.client.force_login(self.seller)
        self.assertEqual(self.client.post(self._delete_url(comment)).status_code, 403)
        self.client.force_login(self.writer)
        self.assertEqual(self.client.get(self._delete_url(comment)).status_code, 405)
        self.assertTrue(AuctionComment.objects.filter(pk=comment.pk).exists())

    def test_bin_visibility(self):
        comment = self._comment()
        for user, visible in ((self.writer, True), (self.staff, True), (self.seller, False)):
            self.client.force_login(user)
            (self.assertContains if visible else self.assertNotContains)(self.client.get(self.detail), self._delete_url(comment))


class AuctionDeactivatePostOnlyTest(TestCase):
    def setUp(self):
        author = Photographer.objects.get_or_create(user=User.objects.create_user(username='d-seller', password='pw-12345678'))[0]
        now = timezone.now()
        self.auction = Auction.objects.create(photo=Photo.objects.create(author=author, image='dummy_image.jpg'),
                                              start_time=now, end_time=now + timedelta(days=1), starting_bid=5)
        self.url = reverse('auction-deactivate', kwargs={'pk': self.auction.pk})
        self.staff = User.objects.create_user(username='d-staff', password='pw-12345678', is_staff=True)

    def test_get_is_refused_and_auction_stays_active(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.auction.refresh_from_db()
        self.assertTrue(self.auction.is_active)

    def test_staff_post_deactivates(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse('auction-list'))
        self.assertIn(f"Аукционът '{self.auction.pk}' е деактивиран.", [str(m) for m in response.context['messages']])
        self.auction.refresh_from_db()
        self.assertFalse(self.auction.is_active)

    def test_regular_user_post_is_forbidden(self):
        self.client.force_login(User.objects.create_user(username='d-user', password='pw-12345678'))
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.auction.refresh_from_db()
        self.assertTrue(self.auction.is_active)


class AuctionBidSectionTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='b-seller', password='pw-12345678')
        photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=self.seller)[0], image='dummy_image.jpg')
        now = timezone.now()
        self.auction = Auction.objects.create(photo=photo, start_time=now, end_time=now + timedelta(days=1), starting_bid=5)
        self.url = reverse('auction-detail', kwargs={'pk': self.auction.pk})
        self.bid_url = reverse('auction-bid', kwargs={'pk': self.auction.pk})
        self.cannot = 'Не можете да направите оферта за този аукцион.'

    def test_logged_out_on_open_auction_gets_login_link(self):
        page = self.client.get(self.url)
        self.assertContains(page, f'href="{reverse("login")}?next={self.url}" class="login-link"')
        self.assertContains(page, 'Влезте, за да направите оферта')
        self.assertNotContains(page, self.cannot)

    def test_signed_in_bidder_gets_form(self):
        self.client.force_login(User.objects.create_user(username='b-buyer', password='pw-12345678'))
        page = self.client.get(self.url)
        self.assertContains(page, f'action="{self.bid_url}"')
        self.assertNotContains(page, 'Влезте, за да направите оферта')
        self.assertContains(page, '<button type="submit" class="text-button text-button-success ms-2"><i class="fas fa-gavel me-1"></i>Направи оферта</button>', html=True)

    def test_seller_and_closed_auction_get_warning(self):
        self.client.force_login(self.seller)
        self.assertContains(self.client.get(self.url), self.cannot)
        self.client.logout()
        Auction.objects.filter(pk=self.auction.pk).update(is_active=False)
        page = self.client.get(self.url)
        self.assertContains(page, self.cannot)
        self.assertNotContains(page, 'Влезте, за да направите оферта')


class AuctionEuroPricesTest(TestCase):
    def test_prices_are_shown_in_euro(self):
        from auctions.models import Bid
        seller = User.objects.create_user(username='eu-seller', password='pw-12345678')
        buyer = User.objects.create_user(username='eu-buyer', password='pw-12345678')
        Photographer.objects.get_or_create(user=buyer)
        photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=seller)[0], image='dummy_image.jpg')
        now = timezone.now()
        auction = Auction.objects.create(photo=photo, start_time=now, end_time=now + timedelta(days=1),
                                         starting_bid=10, current_highest_bid=25, highest_bidder=buyer)
        Bid.objects.create(auction=auction, bidder=buyer, amount=25)
        self.client.force_login(buyer)
        for url in (reverse('auction-list'), reverse('auction-detail', kwargs={'pk': auction.pk})):
            page = self.client.get(url)
            self.assertContains(page, '10.00 €')
            self.assertContains(page, '25.00 €')
            self.assertNotContains(page, 'лв')
        self.assertContains(self.client.get(reverse('auction-detail', kwargs={'pk': auction.pk})), '<span class="input-addon">€</span>', html=True)


class PaymentButtonsTest(TestCase):
    def test_winner_sees_payment_link_and_payment_page_button(self):
        winner = User.objects.create_user(username='winner', password='pw-12345678')
        Photographer.objects.get_or_create(user=winner)
        seller = Photographer.objects.get_or_create(user=User.objects.create_user(username='p-seller', password='pw-12345678'))[0]
        now = timezone.now()
        auction = Auction.objects.create(photo=Photo.objects.create(author=seller, image='dummy_image.jpg'),
                                         start_time=now - timedelta(days=2), end_time=now - timedelta(hours=1),
                                         starting_bid=5, current_highest_bid=30, highest_bidder=winner, is_active=False)
        pay_url = reverse('auction-payment', kwargs={'pk': auction.pk})
        self.client.force_login(winner)
        page = self.client.get(reverse('auction-detail', kwargs={'pk': auction.pk}))
        self.assertContains(page, f'<a href="{pay_url}" class="create-link"><i class="fas fa-credit-card me-1"></i>Към плащане</a>', html=True)
        page = self.client.get(pay_url)
        self.assertContains(page, '<button type="submit" class="text-button text-button-success"><i class="fas fa-credit-card me-1"></i>Завърши плащането</button>', html=True)
