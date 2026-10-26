from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import datetime, timedelta
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